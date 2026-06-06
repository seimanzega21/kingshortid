import requests

API_BASE = 'https://api.shortlovers.id'

def inspect_genres():
    print("--- Fetching Categories ---")
    r = requests.get(f"{API_BASE}/api/categories", timeout=15)
    if r.ok:
        categories = r.json()
        print(f"Categories ({len(categories)}):")
        for c in categories:
            print(f"  - Name: {c.get('name')} | Slug: {c.get('slug')}")
    else:
        print(f"Failed to fetch categories: {r.status_code}")

    print("\n--- Fetching Dramas Sample ---")
    r2 = requests.get(f"{API_BASE}/api/dramas?limit=20", timeout=15)
    if r2.ok:
        data = r2.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        print(f"Sample Dramas ({len(dramas)}):")
        for d in dramas[:10]:
            print(f"  - Title: {d.get('title')} | Genres: {d.get('genres') or d.get('genre')} | CreatedAt: {d.get('createdAt')}")
    else:
        print(f"Failed to fetch dramas: {r2.status_code}")

if __name__ == "__main__":
    inspect_genres()
