"""Check for duplicate dramas in database"""
import psycopg2

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Find Indonesian dramas
cur.execute("""
    SELECT id, title, country, "totalEpisodes", "createdAt"::text,
           LEFT(description, 50) as desc_preview
    FROM "Drama" 
    WHERE country = 'Indonesia'
    ORDER BY title, "createdAt" DESC
""")

dramas = cur.fetchall()

print(f"=== Indonesian Dramas ({len(dramas)} total) ===\n")

# Group by similar titles
from collections import defaultdict
title_groups = defaultdict(list)

for drama in dramas:
    drama_id, title, country, total_eps, created, desc = drama
    
    # Normalize title for grouping (remove spaces, lowercase)
    normalized = title.lower().replace(' ', '').replace('_', '')
    title_groups[normalized].append({
        'id': drama_id,
        'title': title,
        'total_eps': total_eps,
        'created': created,
        'desc': desc
    })

# Find duplicates
print("=== Potential Duplicates ===\n")
duplicates_found = False

for normalized_title, group in title_groups.items():
    if len(group) > 1:
        duplicates_found = True
        print(f"📋 Group: {group[0]['title']}")
        for i, drama in enumerate(group, 1):
            print(f"  {i}. ID: {drama['id'][:8]}... | {drama['total_eps']} eps | {drama['created'][:19]}")
            print(f"     Desc: {drama['desc']}...")
        print()

if not duplicates_found:
    print("✅ No duplicates found!\n")

# Check for dramas with numeric folder-like names (BookIDs in title)
print("=== Dramas with Numeric/BookID Names ===\n")
cur.execute("""
    SELECT id, title, "totalEpisodes"
    FROM "Drama" 
    WHERE country = 'Indonesia' 
      AND (title ~ '^[0-9]+' OR title LIKE '%3100%')
    ORDER BY title
""")

numeric_dramas = cur.fetchall()
if numeric_dramas:
    for drama in numeric_dramas:
        print(f"  {drama[1]} ({drama[2]} eps) - ID: {drama[0][:8]}...")
else:
    print("  ✅ None found")

conn.close()
