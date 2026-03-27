"""
Sync dubbing dramas + episodes to VPS via SSH tunnel
Uses Drizzle table names: dramas, episodes (lowercase)
Reads from local Prisma DB: "Drama", "Episode" (PascalCase)
"""
import psycopg2, sys, re, json
from sshtunnel import SSHTunnelForwarder
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'
DB_HOST_DOCKER = 'supabase-db-og8gwooogk480gcws0o84ssc'
DB_PORT = 5432
DB_USER = 'supabase_admin'
DB_PASS = 'GoZViiH1AXLl73BqLdKDtpeGgwUzfW64'
DB_NAME = 'postgres'
LOCAL_DB = 'postgresql://postgres:seiman21@localhost:5432/kingshort'

print('═' * 60)
print('  Sync Dubbing Dramas → VPS (SSH Tunnel)')
print('═' * 60)

# SSH tunnel
print('\n[1/4] Setting up SSH tunnel...')
import paramiko
paramiko.DSSKey = paramiko.RSAKey  # Fix missing DSSKey
tunnel = SSHTunnelForwarder(
    (SSH_HOST, 22),
    ssh_username=SSH_USER,
    ssh_password=SSH_PASS,
    remote_bind_address=(DB_HOST_DOCKER, DB_PORT),
    local_bind_address=('127.0.0.1', 15432),
    allow_agent=False,
    host_pkey_directories=[],
    ssh_pkey=None,
)
tunnel.start()
print(f'  Tunnel: localhost:{tunnel.local_bind_port}')

VPS_URL = f'postgresql://{DB_USER}:{DB_PASS}@127.0.0.1:{tunnel.local_bind_port}/{DB_NAME}'

# Connect
local = psycopg2.connect(LOCAL_DB)
lcur = local.cursor()
vps = psycopg2.connect(VPS_URL)
vcur = vps.cursor()

# Check VPS table names
vcur.execute("""SELECT table_name FROM information_schema.tables 
               WHERE table_schema='public' AND table_name IN ('dramas','episodes','Drama','Episode','subtitles')""")
vps_tables = [r[0] for r in vcur.fetchall()]
print(f'  VPS tables found: {vps_tables}')

# Determine correct table names
DRAMA_TABLE = 'dramas' if 'dramas' in vps_tables else '"Drama"'
EP_TABLE = 'episodes' if 'episodes' in vps_tables else '"Episode"'
SUB_TABLE = 'subtitles' if 'subtitles' in vps_tables else '"Subtitle"'

# Column name mapping for Drizzle (snake_case) vs Prisma (camelCase)
is_drizzle = 'dramas' in vps_tables

print(f'  Using tables: {DRAMA_TABLE}, {EP_TABLE}')
print(f'  Schema style: {"Drizzle (snake_case)" if is_drizzle else "Prisma (camelCase)"}')

# Count before
vcur.execute(f'SELECT COUNT(*) FROM {DRAMA_TABLE}')
print(f'  VPS dramas before: {vcur.fetchone()[0]}')
vcur.execute(f'SELECT COUNT(*) FROM {EP_TABLE}')
print(f'  VPS episodes before: {vcur.fetchone()[0]}')

# Get dubbing dramas from local
print('\n[2/4] Fetching local dubbing dramas...')
lcur.execute("""SELECT id, title, description, cover, banner, genres::text, 
                       "tagList"::text, "totalEpisodes", rating, views, likes,
                       status, "isVip", "isFeatured", "isActive",
                       "ageRating", director, cast::text, country, language,
                       "createdAt", "updatedAt"
                FROM "Drama" 
                WHERE description LIKE '%%[FRkey:%%' 
                   OR description LIKE '%%Sulih Suara%%' 
                   OR "tagList"::text LIKE '%%Dubbing%%'
                ORDER BY title""")
dramas = lcur.fetchall()
print(f'  Found {len(dramas)} dubbing dramas')

# Sync dramas
print('\n[3/4] Syncing dramas...')
sd, ud = 0, 0

for d in dramas:
    did = d[0]
    title = d[1]
    
    # Parse genres/tagList/cast from text format
    def parse_pg_array(text):
        if not text or text in ('{}', 'NULL'):
            return []
        # Remove braces and split
        inner = text.strip('{}')
        if not inner:
            return []
        return [x.strip('"') for x in inner.split(',')]
    
    genres = parse_pg_array(d[5]) or ['Drama', 'Romance']
    tag_list = parse_pg_array(d[6]) or ['Dubbing']
    cast = parse_pg_array(d[17]) or []
    
    if is_drizzle:
        # Drizzle uses snake_case and jsonb for arrays
        vcur.execute(f'SELECT id FROM {DRAMA_TABLE} WHERE id = %s', (did,))
        if vcur.fetchone():
            # Update existing — fill in missing data
            vcur.execute(f"""UPDATE {DRAMA_TABLE} SET 
                cover = CASE WHEN cover = '' OR cover IS NULL THEN %s ELSE cover END,
                banner = CASE WHEN banner = '' OR banner IS NULL THEN %s ELSE banner END,
                genres = %s::jsonb,
                tag_list = %s::jsonb,
                total_episodes = %s,
                country = %s,
                language = %s,
                updated_at = NOW()
                WHERE id = %s""", (
                d[3] or '', d[4] or '',
                json.dumps(genres), json.dumps(tag_list),
                d[7], d[18] or 'China', d[19] or 'Indonesia',
                did
            ))
            ud += 1
        else:
            # Insert new
            vcur.execute(f"""INSERT INTO {DRAMA_TABLE} 
                (id, title, description, cover, banner, genres, tag_list,
                 total_episodes, rating, views, likes, status, 
                 is_vip, is_featured, is_active, age_rating,
                 director, cast, country, language,
                 created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,
                        %s,%s,%s,%s,%s,
                        %s,%s,%s,%s,
                        %s,%s::jsonb,%s,%s,
                        %s,%s)""", (
                did, title, d[2], d[3] or '', d[4] or '',
                json.dumps(genres), json.dumps(tag_list),
                d[7], d[8] or 0, d[9] or 0, d[10] or 0, d[11] or 'ongoing',
                d[12] or False, d[13] or False, d[14] or False, d[15] or 'all',
                d[16], json.dumps(cast), d[18] or 'China', d[19] or 'Indonesia',
                d[20], d[21]
            ))
            sd += 1
    
    print(f'  {"+" if sd > ud else "~"} {title[:50]}')

vps.commit()
print(f'  ✓ New: {sd}, Updated: {ud}')

# Sync episodes
print('\n[4/4] Syncing episodes...')
se, ke = 0, 0

for d in dramas:
    did = d[0]
    title = d[1]
    
    lcur.execute("""SELECT id, "dramaId", "episodeNumber", title, description, 
                           thumbnail, "videoUrl", duration,
                           "isVip", "coinPrice", views, "isActive",
                           "releaseDate", "createdAt", "updatedAt"
                    FROM "Episode" WHERE "dramaId" = %s
                    ORDER BY "episodeNumber" """, (did,))
    eps = lcur.fetchall()
    
    if not eps:
        continue
    
    ep_added = 0
    for ep in eps:
        if is_drizzle:
            vcur.execute(f'SELECT id FROM {EP_TABLE} WHERE id = %s', (ep[0],))
            if vcur.fetchone():
                ke += 1
                continue
            
            vcur.execute(f"""INSERT INTO {EP_TABLE}
                (id, drama_id, episode_number, title, description,
                 thumbnail, video_url, duration,
                 is_vip, coin_price, views, is_active,
                 release_date, created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (
                ep[0], ep[1], ep[2], ep[3], ep[4] or '',
                ep[5] or '', ep[6], ep[7] or 0,
                ep[8] or False, ep[9] or 0, ep[10] or 0, ep[11] or False,
                ep[12] or ep[13], ep[13], ep[14]
            ))
            se += 1
            ep_added += 1
    
    if ep_added > 0:
        print(f'  + {title[:40]:40s} +{ep_added} episodes')

vps.commit()
print(f'  ✓ New episodes: {se}, Skipped: {ke}')

# Final verification
vcur.execute(f'SELECT COUNT(*) FROM {DRAMA_TABLE}')
print(f'\n  VPS dramas after: {vcur.fetchone()[0]}')
vcur.execute(f'SELECT COUNT(*) FROM {EP_TABLE}')
print(f'  VPS episodes after: {vcur.fetchone()[0]}')

# Sample check
vcur.execute(f"""SELECT title, cover, total_episodes FROM {DRAMA_TABLE} 
                 WHERE description LIKE '%%FRkey%%' LIMIT 3""")
print('\n  Sample VPS dubbing dramas:')
for r in vcur.fetchall():
    cover_ok = 'YES' if r[1] and r[1] != '' else 'NO'
    print(f'    {r[0][:40]:40s} cover={cover_ok} eps={r[2]}')

print('\n' + '═' * 60)
print('  DONE')
print('═' * 60)

vps.close()
local.close()
tunnel.stop()
