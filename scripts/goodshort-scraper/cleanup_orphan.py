import psycopg2

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Find drama we just inserted
cur.execute("""
    SELECT id, title, "createdAt"::text
    FROM "Drama" 
    WHERE title LIKE '%Cinta%Waktu%Tepat%'
    ORDER BY "createdAt" DESC
    LIMIT 1
""")

result = cur.fetchone()
if result:
    drama_id = result[0]
    title = result[1]
    created = result[2]
    
    print(f"Found drama: {title}")
    print(f"  ID: {drama_id}")
    print(f"  Created: {created}")
    
    # Check episodes
    cur.execute(f"""
        SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = '{drama_id}'
    """)
    ep_count = cur.fetchone()[0]
    print(f"  Episodes: {ep_count}")
    
    # If drama exists but has 0 episodes, we need to delete and re-import
    if ep_count == 0:
        print("\n⚠️ Drama exists but has NO episodes - deleting to re-import...")
        cur.execute(f"""DELETE FROM "Drama" WHERE id = '{drama_id}'""")
        conn.commit()
        print("✅ Deleted drama")
else:
    print("No drama found")

conn.close()
