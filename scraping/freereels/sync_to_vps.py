"""Sync to VPS DB via SSH tunnel using paramiko directly"""
import psycopg2, sys, paramiko
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

print('Setting up SSH tunnel...')
tunnel = SSHTunnelForwarder(
    (SSH_HOST, 22),
    ssh_username=SSH_USER,
    ssh_password=SSH_PASS,
    remote_bind_address=(DB_HOST_DOCKER, DB_PORT),
    local_bind_address=('127.0.0.1', 15432),
    allow_agent=False,
    host_pkey_directories=[],
)
tunnel.start()
print(f'Tunnel: localhost:{tunnel.local_bind_port}')

VPS_URL = f'postgresql://{DB_USER}:{DB_PASS}@127.0.0.1:{tunnel.local_bind_port}/{DB_NAME}'

local = psycopg2.connect(LOCAL_DB)
lcur = local.cursor()
vps = psycopg2.connect(VPS_URL)
vcur = vps.cursor()

vcur.execute('SELECT COUNT(*) FROM "Drama"')
print(f'VPS dramas before: {vcur.fetchone()[0]}')

lcur.execute("""SELECT id, title, description, cover, "totalEpisodes", "isActive",
                       "tagList", "createdAt", "updatedAt"
               FROM "Drama" 
               WHERE description LIKE '%%Sulih Suara%%' OR "tagList"::text LIKE '%%Dubbing%%'""")
dramas = lcur.fetchall()
print(f'Local dramas to sync: {len(dramas)}')

sd, se, kd, ke = 0, 0, 0, 0

for d in dramas:
    did, title = d[0], d[1]
    vcur.execute('SELECT id FROM "Drama" WHERE id = %s', (did,))
    if vcur.fetchone():
        vcur.execute("""UPDATE "Drama" SET "tagList" = '{Dubbing}', "isActive" = true, 
                        "totalEpisodes" = %s WHERE id = %s""", (d[4], did))
        kd += 1
    else:
        vcur.execute("""INSERT INTO "Drama" (id,title,description,cover,"totalEpisodes",
                        "isActive","tagList","createdAt","updatedAt")
                        VALUES (%s,%s,%s,%s,%s,true,'{Dubbing}',%s,%s)""",
                     (did, title, d[2], d[3] or '', d[4], d[7], d[8]))
        sd += 1
    
    lcur.execute("""SELECT id,"dramaId","episodeNumber",title,"videoUrl",duration,
                          "isActive","createdAt","updatedAt"
                    FROM "Episode" WHERE "dramaId" = %s""", (did,))
    for ep in lcur.fetchall():
        vcur.execute('SELECT id FROM "Episode" WHERE id = %s', (ep[0],))
        if vcur.fetchone():
            ke += 1; continue
        vcur.execute("""INSERT INTO "Episode" (id,"dramaId","episodeNumber",title,"videoUrl",
                        duration,"isActive","createdAt","updatedAt")
                        VALUES (%s,%s,%s,%s,%s,%s,true,%s,%s)""",
                     (ep[0],ep[1],ep[2],ep[3],ep[4],ep[5],ep[7],ep[8]))
        se += 1
    print(f'  {title[:45]}')

vps.commit()
vcur.execute('SELECT COUNT(*) FROM "Drama"')
print(f'\nVPS dramas after: {vcur.fetchone()[0]}')
print(f'Synced: {sd} dramas, {se} episodes | Skipped: {kd} dramas, {ke} episodes')
vps.close(); local.close(); tunnel.stop()
