"""Quick DB status check for admin panel verification"""
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# All Dubbing dramas
cur.execute("""SELECT d.id, d.title, d."totalEpisodes", d."isActive", d."tagList",
               (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = d.id) as actual_eps,
               (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = d.id AND "isActive" = true) as active_eps
               FROM "Drama" d 
               WHERE d.description LIKE '%Sulih Suara%' OR d."tagList"::text LIKE '%Dubbing%'
               ORDER BY d.title""")
rows = cur.fetchall()

print(f'{"Title":<45s} {"Total":>5s} {"Actual":>6s} {"Active":>6s} {"Tag":>10s}')
print('-' * 80)
total_actual = 0
for r in rows:
    title = r[1][:44]
    total_actual += r[5]
    print(f'{title:<45s} {r[2] or 0:>5d} {r[5]:>6d} {r[6]:>6d} {str(r[4] or "")[:10]:>10s}')

print(f'\nTotal dramas: {len(rows)}, Total episodes in DB: {total_actual}')
conn.close()
