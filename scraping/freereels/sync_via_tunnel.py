"""Sync Dubbing dramas to VPS - FIXED version with error handling"""
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

LOCAL = 'postgresql://postgres:seiman21@localhost:5432/kingshort'
VPS = 'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@127.0.0.1:15432/postgres'

local = psycopg2.connect(LOCAL)
lcur = local.cursor()
vps = psycopg2.connect(VPS)
vps.autocommit = False
vcur = vps.cursor()

lcur.execute("""SELECT id, title, description, cover, "totalEpisodes", "isActive",
                       "tagList", "createdAt", "updatedAt"
               FROM "Drama" 
               WHERE description LIKE '%%Sulih Suara%%' OR "tagList"::text LIKE '%%Dubbing%%'""")
dramas = lcur.fetchall()
print(f'Local Dubbing dramas: {len(dramas)}')

sd, se, kd, ke, fe = 0, 0, 0, 0, 0

for d in dramas:
    did, title = d[0], d[1]
    
    try:
        vcur.execute('SELECT id FROM dramas WHERE id = %s', (did,))
        if vcur.fetchone():
            vcur.execute("""UPDATE dramas SET tag_list = '["Dubbing"]'::jsonb, is_active = true, 
                            total_episodes = %s WHERE id = %s""", (d[4], did))
            kd += 1
        else:
            vcur.execute("""INSERT INTO dramas (id, title, description, cover, total_episodes,
                            is_active, tag_list, created_at, updated_at)
                            VALUES (%s,%s,%s,%s,%s,true,'["Dubbing"]'::jsonb,NOW(),NOW())""",
                         (did, title, d[2], d[3] or '', d[4] or 0))
            sd += 1
        vps.commit()
    except Exception as e:
        vps.rollback()
        print(f'  DRAMA ERROR {title[:30]}: {str(e)[:80]}')
        continue
    
    # Get local episodes (Prisma camelCase)
    lcur.execute("""SELECT id, "dramaId", "episodeNumber", title, "videoUrl", duration
                    FROM "Episode" WHERE "dramaId" = %s ORDER BY "episodeNumber" """, (did,))
    eps = lcur.fetchall()
    ep_synced = 0
    
    for ep in eps:
        try:
            vcur.execute('SELECT id FROM episodes WHERE id = %s', (ep[0],))
            if vcur.fetchone():
                ke += 1; continue
            vcur.execute("""INSERT INTO episodes (id, drama_id, episode_number, title, video_url,
                            duration, is_active, release_date, created_at, updated_at)
                            VALUES (%s,%s,%s,%s,%s,%s,true,NOW(),NOW(),NOW())""",
                         (ep[0], ep[1], ep[2], ep[3] or f'Episode {ep[2]}', ep[4], ep[5] or 60))
            vps.commit()
            se += 1
            ep_synced += 1
        except Exception as e:
            vps.rollback()
            fe += 1
            if fe <= 3:
                print(f'    EP ERROR ep{ep[2]}: {str(e)[:100]}')
    
    print(f'  {title[:45]:45s} synced={ep_synced}/{len(eps)}')

vcur.execute('SELECT COUNT(*) FROM dramas')
after = vcur.fetchone()[0]
print(f'\nVPS dramas: {after}')
print(f'Dramas: +{sd} new, {kd} updated')
print(f'Episodes: +{se} new, {ke} skipped, {fe} failed')
vps.close(); local.close()
print('DONE!')
