"""Parse second drama URLs and register in DB"""
import json, sys, uuid, re
import psycopg2
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load and parse
with open(r'C:\Users\Seiman\Downloads\freereels_urls_2.json') as f:
    urls = json.load(f)

m3u8 = [u for u in urls if '.m3u8' in u]
srt = [u for u in urls if '.srt' in u]
h264 = [u for u in m3u8 if 'h264' in u]
print(f'Total URLs: {len(urls)}, m3u8: {len(m3u8)}, srt: {len(srt)}, h264/episodes: {len(h264)}')

# Group into episodes
episodes = []
ep = None
for u in urls:
    if 'h264' in u and '.m3u8' in u:
        if ep: episodes.append(ep)
        ep = {'h264': u, 'h265': '', 'srts': []}
    elif 'h265' in u and '.m3u8' in u and ep:
        ep['h265'] = u
    elif '.srt' in u and ep:
        ep['srts'].append(u)
if ep: episodes.append(ep)

print(f'Episodes: {len(episodes)}')

# Drama name from tab title: "Ikatan Terlarang"
drama_name = 'Ikatan Terlarang (Sulih Suara)'
drama_slug = 'ikatan-terlarang'
fr_key = 'unknown'  # We need to get this from the URL

# Extract fr_key from the browser URL
# User was on: m.mydramawave.com/series/XXXXX
# We can get it from the m3u8 metadata or we ask user
print(f'\nDrama: {drama_name}')
print(f'Slug: {drama_slug}')

# Save parsed
output = {
    'drama': drama_name,
    'total_episodes': len(episodes),
    'episodes': [{'number': i+1, 'h264': e['h264'], 'h265': e['h265'], 'subtitles': e['srts']} for i, e in enumerate(episodes)]
}
with open(f'd:\\kingshortid\\scraping\\freereels\\parsed_{drama_slug}.json', 'w') as f:
    json.dump(output, f, indent=2)
print(f'Saved parsed_{drama_slug}.json')

# Register in DB
conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Check if exists
cur.execute("""SELECT id FROM "Drama" WHERE title LIKE %s""", (f'%Ikatan Terlarang%',))
existing = cur.fetchone()
if existing:
    print(f'Drama already exists: {existing[0]}')
else:
    drama_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO "Drama" (id, title, description, cover, "totalEpisodes",
                            "isActive", "createdAt", "updatedAt")
        VALUES (%s, %s, %s, %s, %s, false, NOW(), NOW())
        RETURNING id
    """, (drama_id, drama_name,
          f'Drama Ikatan Terlarang. Audio Indonesia (Sulih Suara). [FRkey:{drama_slug}]',
          '', len(episodes)))
    conn.commit()
    print(f'Created drama: {drama_id}')

conn.close()
