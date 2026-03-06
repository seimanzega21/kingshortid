import psycopg2

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Check Indonesian dramas
cur.execute("""
    SELECT id, title, "isActive", "isFeatured", country, "totalEpisodes", "createdAt" 
    FROM "Drama" 
    WHERE country = 'Indonesia' 
    ORDER BY "createdAt" DESC
""")
rows = cur.fetchall()

print(f'\n=== Indonesian Dramas ({len(rows)} total) ===\n')
for r in rows:
    print(f'Title: {r[1]}')
    print(f'  Active: {r[2]} | Featured: {r[3]} | Episodes: {r[5]} | Created: {r[6]}')
    print()

# Check for GoodShort specifically
cur.execute("""
    SELECT id, title, "isActive", description 
    FROM "Drama" 
    WHERE description LIKE '%BookID%'
""")
goodshort = cur.fetchall()

print(f'\n=== GoodShort Dramas (BookID in description) ({len(goodshort)} total) ===\n')
for g in goodshort:
    print(f'Title: {g[1]}')
    print(f'  Active: {g[2]}')
    print(f'  Description: {g[3][:100]}...')
    print()

conn.close()
