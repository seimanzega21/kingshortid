import requests

API_BASE = 'https://api.shortlovers.id'

def find_drama():
    r = requests.get(f"{API_BASE}/api/dramas?limit=1000", timeout=30)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        for d in dramas:
            if d.get('totalEpisodes') == 73:
                print(f"MATCH: {d['title']} | ID: {d['id']}")
            if 'Romantis' in d['title']:
                 print(f"TITLE MATCH: {d['title']} | ID: {d['id']}")
    else:
        print(f"Error: {r.status_code}")

if __name__ == "__main__":
    find_drama()
