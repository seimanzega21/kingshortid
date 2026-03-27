"""Analyze ALL exported drama JSON files, register in DB, and create parsed episodes"""
import json, sys, os, uuid, re, glob
import psycopg2
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DOWNLOADS = r'C:\Users\Seiman\Downloads'
OUTPUT_DIR = r'd:\kingshortid\scraping\freereels'

# Skip non-drama files
SKIP = ['freereels_all_dramas', 'freereels_urls', 'google-services', 'kingshort-']

# Find all drama JSONs
files = glob.glob(os.path.join(DOWNLOADS, '*.json'))
drama_files = []
for f in sorted(files):
    fname = os.path.basename(f)
    if any(s in fname for s in SKIP):
        continue
    drama_files.append(f)

print(f'Found {len(drama_files)} drama JSON files\n')

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Get existing FRkey dramas
cur.execute("""SELECT title, substring(description from '\\[FRkey:([^\\]]+)\\]') FROM "Drama" WHERE description LIKE '%[FRkey:%'""")
existing_keys = {r[1]: r[0] for r in cur.fetchall()}

total_eps_all = 0
dramas_info = []

for fpath in drama_files:
    fname = os.path.basename(fpath)
    title_raw = fname.replace('.json', '').replace('_', ' ').strip()
    
    try:
        with open(fpath) as f:
            urls = json.load(f)
    except:
        print(f'  SKIP (invalid JSON): {fname}')
        continue
    
    if not isinstance(urls, list) or len(urls) == 0:
        print(f'  SKIP (empty/wrong format): {fname}')
        continue
    
    # Count episodes
    h264 = [u for u in urls if isinstance(u, str) and '.m3u8' in u and 'h264' in u]
    srts = [u for u in urls if isinstance(u, str) and '.srt' in u]
    
    if len(h264) == 0:
        print(f'  SKIP (no episodes): {fname}')
        continue
    
    # Group into episodes
    episodes = []
    ep = None
    for u in urls:
        if not isinstance(u, str):
            continue
        if 'h264' in u and '.m3u8' in u:
            if ep: episodes.append(ep)
            ep = {'h264': u, 'h265': '', 'srts': []}
        elif 'h265' in u and '.m3u8' in u and ep:
            ep['h265'] = u
        elif '.srt' in u and ep:
            ep['srts'].append(u)
    if ep: episodes.append(ep)
    
    ep_count = len(episodes)
    total_eps_all += ep_count
    
    # Create slug
    slug = re.sub(r'[^a-z0-9]+', '-', title_raw.lower()).strip('-')[:40]
    
    print(f'{ep_count:3d} eps | {title_raw[:50]:50s} | slug={slug}')
    
    # Save parsed episodes JSON
    output = {
        'drama': title_raw,
        'total_episodes': ep_count,
        'episodes': [{'number': i+1, 'h264': e['h264'], 'h265': e['h265'], 'subtitles': e['srts']} 
                     for i, e in enumerate(episodes)]
    }
    parsed_path = os.path.join(OUTPUT_DIR, f'parsed_{slug}.json')
    with open(parsed_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    # Register in DB if not exists
    cur.execute("""SELECT id FROM "Drama" WHERE title LIKE %s""", (f'%{title_raw[:20]}%',))
    existing = cur.fetchone()
    if existing:
        drama_id = existing[0]
        status = 'EXISTS'
    else:
        drama_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO "Drama" (id, title, description, cover, "totalEpisodes",
                                "isActive", "tagList", "createdAt", "updatedAt")
            VALUES (%s, %s, %s, %s, %s, false, %s, NOW(), NOW())
        """, (drama_id, title_raw, 
              f'Drama Indonesia (Sulih Suara). [FRkey:{slug}]',
              '', ep_count, '{Dubbing}'))
        conn.commit()
        status = 'CREATED'
    
    dramas_info.append({
        'title': title_raw, 'slug': slug, 'episodes': ep_count, 
        'drama_id': drama_id, 'status': status, 'parsed_json': f'parsed_{slug}.json'
    })

conn.close()

print(f'\n{"="*60}')
print(f'TOTAL: {len(dramas_info)} dramas, {total_eps_all} episodes')
print(f'{"="*60}')

# Save master list
with open(os.path.join(OUTPUT_DIR, 'all_dramas_master.json'), 'w') as f:
    json.dump(dramas_info, f, indent=2)
print(f'Saved all_dramas_master.json')
