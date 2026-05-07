import requests

API_BASE = 'https://api.shortlovers.id'

def list_dramas():
    r = requests.get(f"{API_BASE}/api/dramas?limit=500", timeout=15)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        for d in dramas:
            if 'Romantis' in d['title']:
                print(f"MATCH: {d['title']} | ID: {d['id']}")
    else:
        print(f"Error: {r.status_code}")

if __name__ == "__main__":
    list_dramas()
