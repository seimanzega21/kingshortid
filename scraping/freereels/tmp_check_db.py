import psycopg2

LOCAL_DB = 'postgresql://postgres:seiman21@localhost:5432/kingshort'
conn = psycopg2.connect(LOCAL_DB)
cur = conn.cursor()

cur.execute("""
    SELECT d.id, d.title, d."isActive",
           (SELECT COUNT(*) FROM "Episode" e WHERE e."dramaId" = d.id) as ep_count,
           (SELECT COUNT(*) FROM "Episode" e WHERE e."dramaId" = d.id AND e."videoUrl" LIKE '%%stream.shortlovers.id/freereels%%') as r2_eps,
           (SELECT COUNT(*) FROM "Episode" e WHERE e."dramaId" = d.id AND e."videoUrl" LIKE '%%mydramawave%%') as cdn_eps
    FROM "Drama" d 
    WHERE d.title ILIKE '%%Sulih%%' OR d.title ILIKE '%%sulih suara%%'
       OR d.cover LIKE '%%freereels%%' OR d.cover LIKE '%%mydramawave%%'
    ORDER BY d.title
""")

dramas = cur.fetchall()
print(f"FreeReels dramas in DB: {len(dramas)}")
print()

total_r2 = 0
total_cdn = 0
total_eps = 0

for d in dramas:
    did, title, active, eps, r2_eps, cdn_eps = d
    total_r2 += r2_eps
    total_cdn += cdn_eps
    total_eps += eps
    act = "Y" if active else "N"
    print(f"  [{act}] {title[:50]:50s} | {eps:3d} eps | R2:{r2_eps:3d} | CDN:{cdn_eps:3d}")

print(f"\nTotals: {total_eps} eps, {total_r2} R2, {total_cdn} CDN, {total_eps - total_r2 - total_cdn} other")
conn.close()
