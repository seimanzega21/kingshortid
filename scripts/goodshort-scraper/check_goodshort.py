import psycopg2

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Get total counts
cur.execute('SELECT COUNT(*) FROM "Drama"')
total_dramas = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM "Episode"')
total_eps = cur.fetchone()[0]

print(f"\nTotal Dramas: {total_dramas}")
print(f"Total Episodes: {total_eps}\n")

# Check for GoodShort specifically
cur.execute("""
    SELECT id, title, "totalEpisodes", "createdAt"::text
    FROM "Drama" 
    WHERE description LIKE '%BookID%'
    ORDER BY "createdAt" DESC
""")

goodshort = cur.fetchall()

print(f"GoodShort Dramas (with BookID marker): {len(goodshort)}\n")
for g in goodshort:
    print(f"  - {g[1]} ({g[2]} eps) - Created: {g[3][:19]}")
    
    # Count actual episodes
    cur.execute(f'SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = \'{g[0]}\'')
    actual_eps = cur.fetchone()[0]
    print(f"    Actual episodes in DB: {actual_eps}")

conn.close()
