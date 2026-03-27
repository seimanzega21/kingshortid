import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Show current state
cur.execute("""
    SELECT d.title, COUNT(e.id) as ep_count
    FROM "Drama" d
    JOIN "Episode" e ON e."dramaId" = d.id
    WHERE d.description LIKE '%[FRkey:%' AND e."isActive" = false
    GROUP BY d.id, d.title
    ORDER BY d.title
""")
rows = cur.fetchall()
print('Pending episodes per drama:')
for r in rows:
    print(f'  {str(r[0])[:50]}: {r[1]} episodes')

# Count total pending
cur.execute("""
    SELECT COUNT(e.id)
    FROM "Episode" e
    JOIN "Drama" d ON e."dramaId" = d.id
    WHERE d.description LIKE '%[FRkey:%' AND e."isActive" = false
""")
total_pending = cur.fetchone()[0]
print(f'\nTotal pending: {total_pending}')

# ACTIVATE ALL pending episodes for freereels dramas
confirm = input('\nAktifkan semua pending episodes? (y/n): ')
if confirm.lower() == 'y':
    cur.execute("""
        UPDATE "Episode" e
        SET "isActive" = true, "updatedAt" = NOW()
        FROM "Drama" d
        WHERE e."dramaId" = d.id
        AND d.description LIKE '%[FRkey:%'
        AND e."isActive" = false
    """)
    updated = cur.rowcount
    
    # Also update Drama isActive
    cur.execute("""
        UPDATE "Drama" 
        SET "isActive" = true, "updatedAt" = NOW()
        WHERE description LIKE '%[FRkey:%'
        AND "isActive" = false
    """)
    drama_updated = cur.rowcount
    
    conn.commit()
    print(f'\n✅ Activated {updated} episodes, {drama_updated} dramas')
else:
    print('Dibatalkan')

conn.close()
