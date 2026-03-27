"""
Import FreeReels dramas + episodes into LOCAL Prisma DB
=======================================================
Reads from pipeline_v2_status.json and parsed JSONs.
Uses Prisma-style camelCase column names.
"""
import psycopg2, json, sys, re, uuid
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

LOCAL_DB = 'postgresql://postgres:seiman21@localhost:5432/kingshort'
R2_PUBLIC = 'https://stream.shortlovers.id'
SCRIPT_DIR = Path(__file__).parent
STATUS_FILE = SCRIPT_DIR / 'pipeline_v2_status.json'
SERIES_IDS_FILE = SCRIPT_DIR / 'freereels_series_ids.json'

def load_cover_map():
    if not SERIES_IDS_FILE.exists():
        return {}
    raw = json.loads(SERIES_IDS_FILE.read_text(encoding='utf-8'))
    covers = {}
    for k, v in raw.items():
        if isinstance(v, dict) and v.get('cover'):
            key = v.get('title', k).lower().strip()
            covers[key] = v['cover']
    return covers

def find_cover(title, cover_map, parsed_data, info):
    if info.get('cover_url'):
        return info['cover_url']
    cover = parsed_data.get('cover', '')
    t = re.sub(r'\(sulih suara\)', '', title.lower().strip(), flags=re.IGNORECASE).strip()
    for k, url in cover_map.items():
        clean_k = re.sub(r'\(sulih suara\)', '', k, flags=re.IGNORECASE).strip()
        if clean_k and t and (clean_k in t or t in clean_k):
            return url
    return cover

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--limit', type=int)
    a = p.parse_args()

    print('═' * 60)
    print('  FreeReels → LOCAL Prisma DB Import')
    print('═' * 60)
    print(f'  Mode: {"DRY-RUN" if a.test else "PRODUCTION"}')

    status = json.loads(STATUS_FILE.read_text(encoding='utf-8'))
    complete = {k: v for k, v in status.items() if v.get('complete')}
    cover_map = load_cover_map()
    print(f'  Complete dramas: {len(complete)}')
    print(f'  Cover map: {len(cover_map)} entries')

    if a.limit:
        complete = dict(list(complete.items())[:a.limit])

    # Connect to local DB
    conn = psycopg2.connect(LOCAL_DB)
    conn.autocommit = False
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM "Drama"')
    print(f'  Local dramas before: {cur.fetchone()[0]}')
    cur.execute('SELECT COUNT(*) FROM "Episode"')
    print(f'  Local episodes before: {cur.fetchone()[0]}')

    print(f'\n{"─" * 60}')
    d_new = d_upd = d_skip = 0
    e_new = e_upd = 0

    for parsed_key, info in complete.items():
        title = info.get('title', '?')
        folder = info.get('folder', '')
        r2_urls = info.get('r2_urls', {})
        total_eps = info.get('total', 0)

        # Load parsed JSON
        parsed_file = SCRIPT_DIR / parsed_key
        parsed_data = {}
        if parsed_file.exists():
            parsed_data = json.loads(parsed_file.read_text(encoding='utf-8'))

        clean_title = re.sub(r'\(Sulih Suara\)', '', title, flags=re.IGNORECASE).strip()
        desc = parsed_data.get('description', '') or 'Drama pendek Indonesia dengan sulih suara.'
        genres = ['Drama', 'Romance']
        tags = ['Dubbing']
        cover = find_cover(title, cover_map, parsed_data, info)

        if a.test:
            print(f'  [DRY] {clean_title[:45]:45s} | {len(r2_urls)} eps | cov={"Y" if cover else "N"}')
            d_new += 1
            continue

        # Check existing by title similarity
        search = clean_title[:30].replace("'", "''")
        cur.execute(
            """SELECT id FROM "Drama" WHERE title ILIKE %s LIMIT 1""",
            (f'%{search}%',)
        )
        existing = cur.fetchone()

        if existing:
            drama_id = existing[0]
            # Update metadata
            cur.execute("""UPDATE "Drama" SET 
                cover = CASE WHEN cover = '' OR cover IS NULL THEN %s ELSE cover END,
                "totalEpisodes" = %s,
                "updatedAt" = NOW()
                WHERE id = %s""", (cover, total_eps, drama_id))
            d_upd += 1
            action = '~'
        else:
            drama_id = str(uuid.uuid4())
            cur.execute("""INSERT INTO "Drama" 
                (id, title, description, cover, banner, genres, "tagList",
                 "totalEpisodes", rating, views, likes, "reviewCount", "averageRating",
                 status, "isVip", "isFeatured", "isActive", "ageRating",
                 director, "cast", country, language,
                 "createdAt", "updatedAt")
                VALUES (%s, %s, %s, %s, %s,
                        %s::text[], %s::text[],
                        %s, 0, 0, 0, 0, 0,
                        'ongoing', false, false, false, 'all',
                        NULL, '{}'::text[], 'China', 'Indonesia',
                        NOW(), NOW())""",
                (drama_id, clean_title, desc, cover, cover,
                 '{' + ','.join(f'"{g}"' for g in genres) + '}',
                 '{' + ','.join(f'"{t}"' for t in tags) + '}',
                 total_eps))
            d_new += 1
            action = '+'

        # Insert/update episodes
        ep_added = 0
        for ep_key, r2_url in sorted(r2_urls.items()):
            ep_num = int(ep_key.split('_')[1])

            cur.execute(
                'SELECT id FROM "Episode" WHERE "dramaId" = %s AND "episodeNumber" = %s',
                (drama_id, ep_num)
            )
            existing_ep = cur.fetchone()

            if existing_ep:
                cur.execute("""UPDATE "Episode" SET "videoUrl" = %s, "updatedAt" = NOW()
                              WHERE id = %s AND "videoUrl" IS DISTINCT FROM %s""",
                            (r2_url, existing_ep[0], r2_url))
                e_upd += 1
            else:
                ep_id = str(uuid.uuid4())
                cur.execute("""INSERT INTO "Episode"
                    (id, "dramaId", "episodeNumber", title, description,
                     thumbnail, "videoUrl", duration,
                     "isVip", "coinPrice", views, "isActive",
                     "releaseDate", "createdAt", "updatedAt")
                    VALUES (%s, %s, %s, %s, '',
                            '', %s, 0,
                            false, 0, 0, true,
                            NOW(), NOW(), NOW())""",
                    (ep_id, drama_id, ep_num, f'Episode {ep_num}', r2_url))
                ep_added += 1
                e_new += 1

        cover_s = 'Y' if cover else 'N'
        print(f'  {action} {clean_title[:45]:45s} | {len(r2_urls):3d} eps (+{ep_added}) | cov={cover_s}')

    if not a.test:
        conn.commit()

        cur.execute('SELECT COUNT(*) FROM "Drama"')
        print(f'\n  Local dramas after: {cur.fetchone()[0]}')
        cur.execute('SELECT COUNT(*) FROM "Episode"')
        print(f'  Local episodes after: {cur.fetchone()[0]}')

    conn.close()

    print(f'\n[Summary]')
    print(f'  Dramas:   +{d_new} new, ~{d_upd} updated')
    print(f'  Episodes: +{e_new} new, ~{e_upd} updated')
    print(f'\n{"═" * 60}')
    print(f'  ✅ Dramas imported with isActive=false (PENDING)')
    print(f'  → Refresh Admin Panel to see episodes')
    print(f'{"═" * 60}')

if __name__ == '__main__':
    main()
