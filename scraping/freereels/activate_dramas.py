"""Activate all Dubbing dramas and check admin panel DB"""
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# 1. Activate all Dubbing dramas
cur.execute("""UPDATE "Drama" SET "isActive" = true 
               WHERE description LIKE '%Sulih Suara%' OR "tagList"::text LIKE '%Dubbing%'""")
print(f'Activated {cur.rowcount} dramas')

# 2. Also activate episodes that have videoUrl
cur.execute("""UPDATE "Episode" SET "isActive" = true 
               WHERE "videoUrl" IS NOT NULL AND "videoUrl" != '' 
               AND "dramaId" IN (SELECT id FROM "Drama" WHERE description LIKE '%Sulih Suara%' OR "tagList"::text LIKE '%Dubbing%')""")
print(f'Activated {cur.rowcount} episodes')

conn.commit()

# 3. Verify
cur.execute("""SELECT d.title, d."isActive", 
               (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = d.id) as eps,
               (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = d.id AND "isActive" = true) as active_eps
               FROM "Drama" d 
               WHERE d.description LIKE '%Sulih Suara%' OR d."tagList"::text LIKE '%Dubbing%'
               ORDER BY d.title""")
for r in cur.fetchall():
    print(f'  {"[ON]" if r[1] else "[OFF]"} {r[0][:45]:45s} eps={r[2]:3d} active={r[3]:3d}')

conn.close()
