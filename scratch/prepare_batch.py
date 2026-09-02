import json
import requests
import urllib.parse
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

API_BASE = 'http://141.11.160.187:3002/api'

def check_duplicate_in_db(title):
    try:
        query = urllib.parse.quote(title)
        url = f"{API_BASE}/dramas?title={query}"
        r = requests.get(url, timeout=10)
        if r.ok:
            data = r.json()
            docs = data.get('docs', [])
            for d in docs:
                if d.get('title', '').strip().lower() == title.strip().lower():
                    return d.get('id')
    except Exception as e:
        pass
    return None

with open('reelshort_top20.json', 'r', encoding='utf-8') as f:
    dramas = json.load(f)

filtered = []
for d in dramas:
    db_id = check_duplicate_in_db(d['title'])
    if db_id:
        print(f"SKIP: {d['title']} (Already in DB ID: {db_id})")
    else:
        print(f"ADD: {d['title']}")
        filtered.append(d)

with open('scratch/queue_reelshort_batch.py', 'w', encoding='utf-8') as f:
    f.write('import subprocess\nimport time\n\n')
    f.write('ids = [\n')
    for d in filtered:
        f.write(f'    "{d["id"]}", # {d["title"]}\n')
    f.write(']\n\n')
    f.write('''for movie_id in ids:
    print(f"\\n=======================================================")
    print(f"Starting REELSHORT scrape for movie_id: {movie_id}")
    print(f"=======================================================\\n")
    
    cmd = ['python', 'scripts/scrape_reelshort_provider.py', movie_id]
    subprocess.run(cmd)
    
    print(f"\\n[QUEUE] Sleeping for 15 seconds before next drama to prevent rate limiting...\\n")
    time.sleep(15)

print("\\nAll batch processing completed successfully!")
''')

print(f"\\nReady to run {len(filtered)} dramas!")
