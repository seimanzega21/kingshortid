import requests

API_BASE = 'https://api.shortlovers.id'

def check():
    # Check if the dramas are still causing issues in the list
    r = requests.get(f"{API_BASE}/api/dramas?limit=50&includeInactive=true", timeout=15)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        problematic = []
        for d in dramas:
            eps = len(d.get('episodes', []))
            if d.get('totalEpisodes', 0) > 0 and eps == 0:
                problematic.append(d)
                print(f"PROBLEM: {d['title']} (ID: {d['id']}) - Total: {d['totalEpisodes']}, But Episodes: 0")
        if not problematic:
            print("Database is clean. No 0-episode dramas found.")
    else:
        print(f"Error fetching dramas: {r.status_code}")

if __name__ == "__main__":
    check()
