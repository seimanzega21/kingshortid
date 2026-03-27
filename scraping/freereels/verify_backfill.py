import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
c = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = c.cursor()
cur.execute("""
    SELECT d.title, 
           CASE WHEN d.cover != '' AND d.cover IS NOT NULL THEN 'YES' ELSE 'NO' END,
           d."totalEpisodes",
           (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = d.id),
           d.genres::text,
           d."isActive"
    FROM "Drama" d 
    WHERE d.description LIKE '%%[FRkey:%%'
    ORDER BY d.title
""")
rows = cur.fetchall()
ok = sum(1 for r in rows if r[1] == 'YES' and r[3] > 0)
print(f'Total FRkey dramas: {len(rows)}')
print(f'OK (cover + episodes): {ok}/{len(rows)}')
print()
for r in rows:
    flag = 'OK' if r[1] == 'YES' and r[3] > 0 else '!!'
    print(f'  [{flag}] {r[0][:40]:40s} cover={r[1]} eps={r[3]:>4}/{r[2]:<4} genres={str(r[4])[:25]:25s} active={r[5]}')
c.close()
