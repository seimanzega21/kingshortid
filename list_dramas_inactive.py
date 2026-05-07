import requests

API_BASE = 'https://api.shortlovers.id'

def list_dramas():
    r = requests.get(f"{API_BASE}/api/dramas?limit=1000&includeInactive=true", timeout=15)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        found = False
        for d in dramas:
            if 'Romantis' in d['title']:
                print(f"MATCH: {d['title']} | ID: {d['id']} | Active: {d.get('isActive')}")
                found = True
        if not found:
            print("No dramas matching 'Romantis' found even with includeInactive=true")
    else:
        print(f"Error: {r.status_code}")

if __name__ == "__main__":
    list_dramas()
