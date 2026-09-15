import requests, json
import urllib3
urllib3.disable_warnings()

API_BASE = 'https://api.shortlovers.id/api'

def get_all_dramas():
    all_dramas = []
    page = 1
    while True:
        url = f"{API_BASE}/dramas?page={page}&limit=100&includeInactive=true"
        r = requests.get(url, timeout=20)
        if not r.ok:
            break
        data = r.json()
        dramas = data.get('dramas', [])
        if not dramas:
            break
        all_dramas.extend(dramas)
        total = data.get('total', 0)
        print(f"Loaded page {page}, total collected: {len(all_dramas)} / {total}")
        if len(all_dramas) >= total:
            break
        page += 1
    return all_dramas

dramas = get_all_dramas()
print(f"Total dramas found: {len(dramas)}")

with open('all_dramas_for_scan.json', 'w', encoding='utf-8') as f:
    json.dump([{'id': d['id'], 'title': d['title'], 'cover': d.get('cover', '')} for d in dramas], f, indent=2, ensure_ascii=False)
