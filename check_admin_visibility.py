import requests

API_BASE = 'https://api.shortlovers.id'

def check_visibility():
    slugs = ['raja-yang-ditakuti-musuh', 'menghabisi-yang-jahat', 'dua-kuasa-menjadi-satu']
    for slug in slugs:
        # Search by title/slug logic
        r = requests.get(f"{API_BASE}/api/dramas?search={slug.replace('-', '%20')}&includeInactive=true", timeout=15)
        if r.ok:
            data = r.json()
            dramas = data if isinstance(data, list) else data.get('dramas', [])
            if dramas:
                d = dramas[0]
                # Check episode count in DB
                er = requests.get(f"{API_BASE}/api/dramas/{d['id']}?includeInactive=true", timeout=15)
                eps_count = len(er.json().get('episodes', [])) if er.ok else 0
                print(f"DRAMA: {d['title']}")
                print(f"  ID: {d['id']}")
                print(f"  Status Active: {d.get('isActive')}")
                print(f"  Episodes in DB: {eps_count}")
                print("-" * 30)
            else:
                print(f"DRAMA {slug} not found in search results.")
        else:
            print(f"Error searching for {slug}: {r.status_code}")

if __name__ == "__main__":
    check_visibility()
