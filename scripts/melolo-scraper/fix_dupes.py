import psycopg2, os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

url = os.getenv('DATABASE_URL').split('?')[0]
conn = psycopg2.connect(url)
cur = conn.cursor()

# Find ALL dramas with duplicate covers
print("=== Finding dramas with duplicate covers ===\n")
cur.execute("""
    SELECT cover, array_agg(id) as ids, array_agg(title) as titles, 
           array_agg((SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = d.id)) as eps
    FROM "Drama" d
    WHERE "isActive" = true AND cover IS NOT NULL AND cover != ''
    GROUP BY cover
    HAVING COUNT(*) > 1
""")
dupes = cur.fetchall()

to_deactivate = []

for cover, ids, titles, eps_counts in dupes:
    print(f"\nDuplicate cover: {cover[:70]}...")
    for i in range(len(ids)):
        print(f"  [{ids[i][:25]}...] {titles[i]} ({eps_counts[i]} eps)")
    
    # Keep the one with the most episodes, deactivate others
    # If same eps count, keep the one with shorter/cleaner title
    best_idx = 0
    best_eps = eps_counts[0]
    for i in range(1, len(ids)):
        if eps_counts[i] > best_eps:
            best_idx = i
            best_eps = eps_counts[i]
        elif eps_counts[i] == best_eps and len(titles[i]) < len(titles[best_idx]):
            best_idx = i
    
    for i in range(len(ids)):
        if i != best_idx:
            to_deactivate.append((ids[i], titles[i], eps_counts[i]))
    
    print(f"  → KEEP: {titles[best_idx]} ({eps_counts[best_idx]} eps)")
    for i in range(len(ids)):
        if i != best_idx:
            print(f"  → DELETE: {titles[i]} ({eps_counts[i]} eps)")

# Execute deletions
if to_deactivate:
    print(f"\n\n{'='*50}")
    print(f"Deactivating {len(to_deactivate)} duplicate dramas:\n")
    for drama_id, title, eps in to_deactivate:
        # Delete episodes first, then deactivate drama
        cur.execute('DELETE FROM "Episode" WHERE "dramaId" = %s', (drama_id,))
        cur.execute('UPDATE "Drama" SET "isActive" = false WHERE id = %s', (drama_id,))
        print(f"  ✅ Deactivated: {title} ({eps} eps deleted)")
    
    conn.commit()
    print(f"\nDone! {len(to_deactivate)} duplicates removed.")
else:
    print("\nNo duplicates to fix.")

# Verify
print(f"\n{'='*50}")
print("Verification:")
cur.execute('SELECT COUNT(*) FROM "Drama" WHERE "isActive" = true')
print(f"  Active dramas: {cur.fetchone()[0]}")
cur.execute('SELECT COUNT(*) FROM "Episode"')
print(f"  Total episodes: {cur.fetchone()[0]}")

cur.close()
conn.close()
