"""Sync R2 URLs from pipeline_v2_status.json → local DB."""
import json, psycopg2

LOCAL_DB = 'postgresql://postgres:seiman21@localhost:5432/kingshort'
STATUS_FILE = 'd:/kingshortid/scraping/freereels/pipeline_v2_status.json'

status = json.load(open(STATUS_FILE, 'r', encoding='utf-8'))
conn = psycopg2.connect(LOCAL_DB)
cur = conn.cursor()

updated_eps = 0
updated_covers = 0
not_found = []

for drama_key, info in status.items():
    title = info.get('title', '')
    r2_urls = info.get('r2_urls', {})
    cover_url = info.get('cover_url', '')
    if not title:
        continue

    # Find by fuzzy title match
    search = title[:30].strip()
    cur.execute("""SELECT id, title FROM "Drama" WHERE title ILIKE %s LIMIT 1""", (f'%{search}%',))
    drama = cur.fetchone()
    if not drama:
        not_found.append(title)
        continue

    drama_id, db_title = drama

    # Update episode videoUrls to R2
    for ep_key, r2_url in r2_urls.items():
        ep_num = int(ep_key.split('_')[1])
        cur.execute("""UPDATE "Episode" SET "videoUrl" = %s 
                      WHERE "dramaId" = %s AND "episodeNumber" = %s 
                      AND ("videoUrl" IS DISTINCT FROM %s)""",
                   (r2_url, drama_id, ep_num, r2_url))
        updated_eps += cur.rowcount

    # Update cover if available
    if cover_url:
        cur.execute("""UPDATE "Drama" SET cover = %s WHERE id = %s 
                      AND (cover IS NULL OR cover NOT LIKE '%%stream.shortlovers%%')""",
                   (cover_url, drama_id))
        updated_covers += cur.rowcount

    print(f"  ✓ {db_title[:45]:45s} → {len(r2_urls)} R2 URLs")

conn.commit()
conn.close()

print(f"\n{'='*50}")
print(f"Updated: {updated_eps} episode URLs, {updated_covers} covers")
if not_found:
    print(f"\nNot found in DB ({len(not_found)}):")
    for t in not_found:
        print(f"  - {t}")
