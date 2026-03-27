"""
Import R2-complete FreeReels dramas → VPS via Docker exec (SSH)
===============================================================
Uses SSH + docker exec psql instead of SSH tunnel (more reliable).
"""
import paramiko, json, sys, re, uuid, time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'
DB_CONTAINER = 'supabase-db-og8gwooogk480gcws0o84ssc'
DB_USER = 'supabase_admin'
DB_NAME = 'postgres'

R2_PUBLIC = 'https://stream.shortlovers.id'
SCRIPT_DIR = Path(__file__).parent
STATUS_FILE = SCRIPT_DIR / 'pipeline_v2_status.json'
SERIES_IDS_FILE = SCRIPT_DIR / 'freereels_series_ids.json'

def ssh_connect():
    paramiko.DSSKey = paramiko.RSAKey
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS)
    return c

def run_sql(ssh, sql, single=False):
    """Run SQL via docker exec psql."""
    escaped = sql.replace("'", "'\\''")
    cmd = f"docker exec {DB_CONTAINER} psql -U {DB_USER} -d {DB_NAME} -t -A -c '{escaped}'"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if err and 'NOTICE' not in err and 'already exists' not in err:
        if 'ERROR' in err:
            raise Exception(f'SQL error: {err}')
    if single:
        return out.split('\n')[0] if out else ''
    return out

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
    """Find best cover URL."""
    # R2 uploaded cover
    if info.get('cover_url'):
        return info['cover_url']
    # Parsed data cover (might be CDN)
    cover = parsed_data.get('cover', '')
    # Cover map by title
    t = re.sub(r'\(sulih suara\)', '', title.lower().strip(), flags=re.IGNORECASE).strip()
    for k, url in cover_map.items():
        clean_k = re.sub(r'\(sulih suara\)', '', k, flags=re.IGNORECASE).strip()
        if clean_k and t and (clean_k in t or t in clean_k):
            return url
    return cover

def esc(s):
    """Escape string for SQL."""
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--limit', type=int)
    a = p.parse_args()

    print('═' * 60)
    print('  FreeReels R2 → VPS Import (Docker Exec)')
    print('═' * 60)
    print(f'  Mode: {"DRY-RUN" if a.test else "PRODUCTION"}')

    status = json.loads(STATUS_FILE.read_text(encoding='utf-8'))
    complete = {k: v for k, v in status.items() if v.get('complete')}
    cover_map = load_cover_map()
    print(f'  Complete dramas: {len(complete)}')
    print(f'  Cover map: {len(cover_map)} entries')

    if a.limit:
        complete = dict(list(complete.items())[:a.limit])

    # Connect SSH
    print('\n[1/4] Connecting SSH...')
    ssh = ssh_connect()
    print('  SSH connected ✓')

    # Test DB
    count = run_sql(ssh, 'SELECT count(*) FROM dramas', single=True)
    print(f'  VPS dramas before: {count}')
    ep_count = run_sql(ssh, 'SELECT count(*) FROM episodes', single=True)
    print(f'  VPS episodes before: {ep_count}')

    # Process dramas
    print(f'\n[2/4] Importing {len(complete)} dramas...\n')
    d_new = d_upd = 0
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
            print(f'  [DRY] {clean_title[:45]:45s} | {len(r2_urls)} eps')
            d_new += 1
            continue

        # Check existing
        search = clean_title[:30].replace("'", "''")
        existing = run_sql(ssh, f"SELECT id FROM dramas WHERE title ILIKE '%{search}%' LIMIT 1", single=True)

        if existing:
            drama_id = existing
            # Update metadata
            run_sql(ssh, f"""UPDATE dramas SET 
                cover = CASE WHEN cover = '' OR cover IS NULL THEN {esc(cover)} ELSE cover END,
                total_episodes = {total_eps},
                updated_at = NOW()
                WHERE id = {esc(drama_id)}""")
            d_upd += 1
            action = '~'
        else:
            # Insert new with is_active=false
            drama_id = run_sql(ssh, f"""INSERT INTO dramas 
                (id, title, description, cover, banner, genres, tag_list,
                 total_episodes, rating, views, likes, review_count, average_rating,
                 status, is_vip, is_featured, is_active, age_rating,
                 director, "cast", country, language,
                 created_at, updated_at)
                VALUES (gen_random_uuid(), {esc(clean_title)}, {esc(desc)}, {esc(cover)}, {esc(cover)},
                        '{json.dumps(genres)}'::jsonb, '{json.dumps(tags)}'::jsonb,
                        {total_eps}, 0, 0, 0, 0, 0,
                        'ongoing', false, false, false, 'all',
                        NULL, '[]'::jsonb, 'China', 'Indonesia',
                        NOW(), NOW())
                RETURNING id""", single=True)
            d_new += 1
            action = '+'

        if not drama_id:
            print(f'  ✗ {clean_title[:45]} — failed to get drama ID')
            continue

        # Insert/update episodes
        ep_added = 0
        for ep_key, r2_url in sorted(r2_urls.items()):
            ep_num = int(ep_key.split('_')[1])

            existing_ep = run_sql(ssh,
                f"SELECT id FROM episodes WHERE drama_id = {esc(drama_id)} AND episode_number = {ep_num}",
                single=True)

            if existing_ep:
                # Update video URL
                run_sql(ssh, f"""UPDATE episodes SET video_url = {esc(r2_url)}, updated_at = NOW()
                              WHERE id = {esc(existing_ep)} AND video_url IS DISTINCT FROM {esc(r2_url)}""")
                e_upd += 1
            else:
                run_sql(ssh, f"""INSERT INTO episodes
                    (id, drama_id, episode_number, title, description,
                     thumbnail, video_url, duration,
                     is_vip, coin_price, views, is_active,
                     release_date, created_at, updated_at)
                    VALUES (gen_random_uuid(), {esc(drama_id)}, {ep_num}, {esc(f'Episode {ep_num}')}, '',
                            '', {esc(r2_url)}, 0,
                            false, 0, 0, false,
                            NOW(), NOW(), NOW())""")
                ep_added += 1
                e_new += 1

        cover_s = 'Y' if cover else 'N'
        print(f'  {action} {clean_title[:45]:45s} | {len(r2_urls):3d} eps (+{ep_added}) | cov={cover_s}')

    # Summary
    print(f'\n[3/4] Summary')
    print(f'  Dramas:   +{d_new} new, ~{d_upd} updated')
    print(f'  Episodes: +{e_new} new, ~{e_upd} updated')

    if not a.test:
        count2 = run_sql(ssh, 'SELECT count(*) FROM dramas', single=True)
        ep_count2 = run_sql(ssh, 'SELECT count(*) FROM episodes', single=True)
        print(f'\n[4/4] Verification')
        print(f'  VPS dramas after:   {count2}')
        print(f'  VPS episodes after: {ep_count2}')

        # Show sample pending
        sample = run_sql(ssh, """SELECT title, is_active, total_episodes FROM dramas 
                                  WHERE is_active = false AND tag_list::text ILIKE '%Dubbing%'
                                  ORDER BY title LIMIT 5""")
        if sample:
            print(f'\n  Pending FreeReels dramas:')
            for line in sample.split('\n'):
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 3:
                        t, active, eps = parts[0].strip(), parts[1].strip(), parts[2].strip()
                        print(f'    [⏸️] {t[:45]:45s} | {eps} eps')

    ssh.close()
    print(f'\n{"═" * 60}')
    print(f'  ⚠️  All dramas imported with is_active=false (PENDING)')
    print(f'  → Go to Admin Panel → Dramas to review and publish')
    print(f'{"═" * 60}')

if __name__ == '__main__':
    main()
