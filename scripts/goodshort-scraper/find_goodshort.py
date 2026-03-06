import psycopg2
import json

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Search for ANY mention of our GoodShort titles
search_terms = ['Waktu', 'Tepat', 'Kedua', 'Sejati', 'Menanti']

for term in search_terms:
    cur.execute(f"""
        SELECT id, title, country, "totalEpisodes", "createdAt"::text
        FROM "Drama" 
        WHERE title LIKE '%{term}%'
    """)
    results = cur.fetchall()
    
    if results:
        print(f'\n=== Dramas containing "{term}" ===')
        for r in results:
            print(f'{r[1]} ({r[2]}) - {r[3]} eps - Created: {r[4][:19]}')
            
            # Get episode count
            cur.execute(f"""
                SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = '{r[0]}'
            """)
            ep_count = cur.fetchone()[0]
            print(f'  -> Actual episodes in DB: {ep_count}')

# Also check newest dramas
print(f'\n\n=== Last 5 Dramas by Creation Date ===')
cur.execute("""
    SELECT d.id, d.title, d.country, d."totalEpisodes", 
           COUNT(e.id) as actual_episodes, d."createdAt"::text
    FROM "Drama" d
    LEFT JOIN "Episode" e ON d.id = e."dramaId"
    GROUP BY d.id
    ORDER BY d."createdAt" DESC
    LIMIT 5
""")
rows = cur.fetchall()

for r in rows:
    print(f'{r[1][:45]:45} | {r[2]:10} | {r[4]:3} eps | {r[5][:19]}')

conn.close()
