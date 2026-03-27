"""
Backfill Dubbing Dramas: Fix missing cover, genres, and episodes
================================================================
Strategy:
  1. Find all dramas with [FRkey:...] in description
  2. Match FRkey to local parsed_*.json files for episode video URLs
  3. Match FRkey to R2 folders for cover images
  4. Update drama records and insert episodes

Run: python backfill_dubbing.py [--test] [--activate]
"""
import psycopg2, sys, re, json, uuid, os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATABASE_URL = 'postgresql://postgres:seiman21@localhost:5432/kingshort'
R2_PUBLIC = 'https://stream.shortlovers.id'
PARSED_DIR = Path(__file__).parent  # Same directory as this script

# Map of R2 folder names for covers (known mappings from R2 scan)
# FRkey (DB description) → R2 folder name (for cover image)
R2_COVER_MAP = {
    'rwcCi67MwS': 'a_mother_wont_hold_back',
    'XHwpplhsu2': 'boss_lady_goes_undercover',
    'eNFDnztZRb': 'bos-kuliah-lagi',
    'h7XYuJo63T': 'from_orphan_to_regents_little_princess',
    'DlZut9JYg3': 'lies_in_love_truth_in_hate',
    'VfjJTqZGw1': 'love_until_it_hurts',
    'Ya8p5nJE5e': 'lucifer_my_boyfriend_from_hell',
    '66408d7f-a58': 'married_strangers_meet_again',
    'Zx4xZRHcVX': 'married_strangers_meet_again',
    'yDTtoDPZ1I': 'mr_fu_your_wifes_secret_identity_is_out_again',
    'Q6v1LCeeqc': 'riding_the_waves_of_the_1980s',
    'nZ8X63ZAFP': 'she_mistook_him_for_love',
    'GLilD9ujl9': 'the_bomb_disposal_expert',
    'mw74vodf8g': 'the_emperors_personal_doctor',
    'fLGCHJFVGx': 'the_mafia_hunter',
}

def find_parsed_file(frkey):
    """Find the local parsed JSON file matching an FRkey."""
    # Direct match: parsed_{frkey}.json
    direct = PARSED_DIR / f'parsed_{frkey}.json'
    if direct.exists():
        return direct
    
    # Try truncated match (FRkeys in DB are often truncated)
    for f in PARSED_DIR.glob('parsed_*.json'):
        if f.name == 'parsed_episodes.json':
            continue
        fname = f.name.replace('parsed_', '').replace('.json', '')
        # Check if FRkey starts with or matches the filename
        if frkey.startswith(fname) or fname.startswith(frkey):
            return f
    
    return None

def get_cover_url(frkey, r2_folder=None):
    """Get R2 cover URL for a drama."""
    # Check known R2 folder mapping
    folder = R2_COVER_MAP.get(frkey) or r2_folder
    if folder:
        return f'{R2_PUBLIC}/freereels/{folder}/cover.jpg'
    
    # Try using FRkey as folder name directly (for slug-style FRkeys)
    # Convert hyphens to underscores as R2 uses underscores
    underscore_key = frkey.replace('-', '_')
    return f'{R2_PUBLIC}/freereels/{underscore_key}/cover.jpg'


def main():
    import argparse
    p = argparse.ArgumentParser(description='Backfill Dubbing Drama Data')
    p.add_argument('--test', action='store_true', help='Dry run')
    p.add_argument('--activate', action='store_true', help='Set dramas and episodes to isActive=true')
    a = p.parse_args()

    print('═' * 60)
    print('  Backfill Dubbing Dramas — Fix Missing Data')
    print('═' * 60)
    print(f'  Mode: {"DRY-RUN" if a.test else "PRODUCTION"}')
    print(f'  Activate: {"YES" if a.activate else "NO"}')
    print()

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    # Find all dramas with FRkey
    cur.execute("""
        SELECT id, title, description, cover, "totalEpisodes",
               (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = d.id) as actual_eps
        FROM "Drama" d
        WHERE description LIKE '%%[FRkey:%%'
        ORDER BY title
    """)
    dramas = cur.fetchall()
    print(f'  Found {len(dramas)} dramas with [FRkey:...]\n')

    updated = 0
    eps_added = 0
    subs_added = 0
    skipped = 0
    failed = 0

    for d in dramas:
        drama_id, title, desc, cover, total_eps, actual_eps = d
        
        # Extract FRkey
        m = re.search(r'\[FRkey:([^\]]+)\]', desc)
        if not m:
            skipped += 1
            continue
        frkey = m.group(1)

        # Check if drama already has episodes
        if actual_eps > 0 and cover and cover != '':
            print(f'  ⊘ {title[:45]:45s} — already has {actual_eps} eps + cover')
            skipped += 1
            continue

        # Find parsed file
        parsed = find_parsed_file(frkey)
        if not parsed:
            print(f'  ✗ {title[:45]:45s} — no parsed file for FRkey:{frkey}')
            skipped += 1
            continue

        # Read parsed data
        try:
            data = json.loads(parsed.read_text(encoding='utf-8'))
        except Exception as e:
            print(f'  ✗ {title[:45]:45s} — parse error: {e}')
            failed += 1
            continue

        episodes = data.get('episodes', [])
        if not episodes:
            print(f'  ✗ {title[:45]:45s} — no episodes in parsed file')
            skipped += 1
            continue

        # Build cover URL
        cover_url = get_cover_url(frkey)
        is_active = a.activate

        if a.test:
            print(f'  [DRY] {title[:45]:45s} eps={len(episodes)} cover={cover_url[:50]}')
            updated += 1
            continue

        try:
            # 1. Update drama record
            cur.execute("""
                UPDATE "Drama" SET 
                    cover = CASE WHEN cover IS NULL OR cover = '' THEN %s ELSE cover END,
                    banner = CASE WHEN banner IS NULL OR banner = '' THEN %s ELSE banner END,
                    genres = CASE WHEN genres IS NULL OR genres = '{}' THEN %s::text[] ELSE genres END,
                    country = 'China',
                    language = 'Indonesia',
                    "totalEpisodes" = %s,
                    "isActive" = %s,
                    "updatedAt" = NOW()
                WHERE id = %s
            """, (
                cover_url, cover_url,
                ['Drama', 'Romance'],
                len(episodes),
                is_active,
                drama_id
            ))

            # 2. Insert episodes
            ep_ok = 0
            for ep in episodes:
                ep_num = ep.get('number', 0)
                # video URL: prefer h264, fallback h265
                video_url = ep.get('h264', '') or ep.get('h265', '')
                if isinstance(video_url, list):
                    video_url = video_url[0] if video_url else ''
                
                subs = ep.get('subtitles', [])
                
                if not video_url or not ep_num:
                    continue

                # Check duplicate
                cur.execute(
                    'SELECT id FROM "Episode" WHERE "dramaId"=%s AND "episodeNumber"=%s',
                    (drama_id, ep_num)
                )
                if cur.fetchone():
                    continue

                ep_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO "Episode" (
                        id, "dramaId", "episodeNumber",
                        title, description, thumbnail, "videoUrl", duration,
                        "isVip", "coinPrice", views,
                        "isActive", "releaseDate",
                        "createdAt", "updatedAt"
                    ) VALUES (
                        %s, %s, %s,
                        %s, '', '', %s, 0,
                        false, 0, 0,
                        %s, NOW(),
                        NOW(), NOW()
                    )
                """, (
                    ep_id, drama_id, ep_num,
                    f'Episode {ep_num}',
                    video_url,
                    is_active,
                ))
                ep_ok += 1
                eps_added += 1

                # 3. Insert subtitle
                if subs:
                    sub_url = subs[0] if isinstance(subs, list) else subs
                    if sub_url and isinstance(sub_url, str):
                        try:
                            cur.execute("""
                                INSERT INTO "Subtitle" (
                                    id, "episodeId", language, label, url, "isDefault", "createdAt"
                                ) VALUES (%s, %s, 'id', 'Bahasa Indonesia', %s, true, NOW())
                            """, (str(uuid.uuid4()), ep_id, sub_url))
                            subs_added += 1
                        except Exception:
                            pass

            conn.commit()
            updated += 1
            print(f'  ✓ {title[:45]:45s} cover=OK +{ep_ok} eps')

        except Exception as e:
            conn.rollback()
            print(f'  ✗ {title[:45]:45s} ERROR: {e}')
            import traceback; traceback.print_exc()
            failed += 1

    # Summary
    print(f'\n{"═" * 60}')
    print(f'  ✓ Dramas updated:    {updated}')
    print(f'  📺 Episodes inserted: {eps_added}')
    print(f'  💬 Subtitles inserted: {subs_added}')
    print(f'  ⊘ Skipped:           {skipped}')
    print(f'  ✗ Failed:            {failed}')
    print(f'{"═" * 60}')

    # Quick verify
    if not a.test:
        cur = conn.cursor()
        cur.execute("""
            SELECT d.title, 
                   CASE WHEN d.cover != '' THEN 'YES' ELSE 'NO' END,
                   d."totalEpisodes",
                   (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = d.id)
            FROM "Drama" d 
            WHERE d.description LIKE '%%[FRkey:%%'
            ORDER BY d.title
        """)
        print(f'\nVerification:')
        for r in cur.fetchall():
            status = '✓' if r[1] == 'YES' and r[3] > 0 else '✗'
            print(f'  {status} {r[0][:40]:40s} cover={r[1]} eps={r[3]}/{r[2]}')
        cur.close()

    conn.close()

if __name__ == '__main__':
    main()
