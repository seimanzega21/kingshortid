import requests
import json
import time

API_BASE = 'http://141.11.160.187:3000'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

def get_existing_titles():
    print("Fetching existing dramas from KingShort DB...")
    r = requests.get(f"{API_BASE}/api/dramas?limit=5000", timeout=15)
    existing = set()
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        for d in dramas:
            t = d.get('title', '').strip().lower()
            if t: existing.add(t)
    print(f"Found {len(existing)} existing titles.")
    return existing

def generate_queue(target_count=20):
    existing = get_existing_titles()
    queue = []
    page = 1
    
    while len(queue) < target_count:
        print(f"Fetching page {page} from dotdrama...")
        url = f"https://vidrama.asia/api/dotdrama?action=list&page={page}"
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if not r.ok:
                print("Error fetching page.")
                break
            dramas = r.json().get('dramas', [])
            if not dramas:
                print("No more dramas returned.")
                break
                
            for d in dramas:
                title = d.get('title', '').strip()
                t_lower = title.lower()
                
                # generate a slug
                slug = "".join([c if c.isalnum() else "-" for c in t_lower])
                slug = "-".join([s for s in slug.split("-") if s])
                
                if t_lower not in existing:
                    # check if already in queue
                    if not any(q['id'] == d.get('id') for q in queue):
                        queue.append({
                            "title": title,
                            "slug": slug,
                            "id": d.get('id'),
                            "lang": "id",
                            "genres": ["Drama"],
                            "status": "pending"
                        })
                        print(f"Added to queue: {title}")
                        if len(queue) == target_count:
                            break
                else:
                    print(f"Skipping (already in DB): {title}")
                    
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)
        page += 1
        
    print(f"Generated queue of {len(queue)} dramas.")
    with open('dotdrama_queue.json', 'w', encoding='utf-8') as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    generate_queue(20)
