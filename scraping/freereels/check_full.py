import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Full breakdown per drama
cur.execute("""
    SELECT 
        d.title,
        COUNT(e.id) AS ep_count,
        SUM(CASE WHEN e."isActive" = true THEN 1 ELSE 0 END) AS active_eps,
        SUM(CASE WHEN e."isActive" = false THEN 1 ELSE 0 END) AS pending_eps
    FROM "Drama" d
    LEFT JOIN "Episode" e ON e."dramaId" = d.id
    WHERE d.description LIKE '%[FRkey:%'
    GROUP BY d.id, d.title
    ORDER BY d.title
""")
rows = cur.fetchall()
print(f'{"Drama":<40} {"Total":>6} {"Active":>7} {"Pending":>8}')
print('-'*65)
for r in rows:
    print(f'{str(r[0])[:40]:<40} {r[1]:>6} {r[2]:>7} {r[3]:>8}')

cur.execute("""
    SELECT 
        SUM(total_count) as total_eps,
        SUM(active_count) as total_active,
        SUM(pending_count) as total_pending
    FROM (
        SELECT 
            COUNT(e.id) as total_count,
            SUM(CASE WHEN e."isActive" = true THEN 1 ELSE 0 END) as active_count,
            SUM(CASE WHEN e."isActive" = false THEN 1 ELSE 0 END) as pending_count
        FROM "Drama" d
        LEFT JOIN "Episode" e ON e."dramaId" = d.id
        WHERE d.description LIKE '%[FRkey:%'
        GROUP BY d.id
    ) sub
""")
r = cur.fetchone()
print(f'\nTOTAL: {r[0]} eps | {r[1]} active | {r[2]} pending')
conn.close()
