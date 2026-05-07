import requests

API_BASE = 'https://api.shortlovers.id'

def find_new_dramas():
    r = requests.get(f"{API_BASE}/api/dramas?limit=20&includeInactive=true", timeout=15)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        print(f"Total dramas in list: {len(dramas)}")
        for d in dramas[:10]:
            print(f"- {d['title']} (ID: {d['id']}) Active: {d.get('isActive')}")
    else:
        print(f"Error: {r.status_code}")

if __name__ == "__main__":
    find_new_dramas()
