"""Update tagList to 'Dubbing' for ALL dramas in master list"""
import json, psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

with open('all_dramas_master.json') as f:
    dramas = json.load(f)

updated = 0
for d in dramas:
    cur.execute("""UPDATE "Drama" SET "tagList" = '{Dubbing}' WHERE id = %s AND ("tagList" IS NULL OR "tagList" != '{Dubbing}')""", (d['drama_id'],))
    if cur.rowcount > 0:
        updated += 1
        print(f'  Updated: {d["title"]}')

# Also update existing FreeReels dramas that have Sulih Suara in title
cur.execute("""UPDATE "Drama" SET "tagList" = '{Dubbing}' WHERE title LIKE '%Sulih Suara%' AND ("tagList" IS NULL OR "tagList" != '{Dubbing}')""")
updated += cur.rowcount

conn.commit()
conn.close()
print(f'\nTotal updated: {updated}')
