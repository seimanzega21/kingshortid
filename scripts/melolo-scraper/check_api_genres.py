import requests, json

API = "https://vidrama.asia/api/melolo"

# Check what genres look like from search
r = requests.get(f"{API}?action=search&keyword=sulit&limit=3", timeout=10)
data = r.json().get("data", [])
print("=== SEARCH RESULT ===")
for d in data[:2]:
    print(f"  {d['title']}")
    print(f"    genres key: {d.get('genres', 'NOT FOUND')}")
    print(f"    all keys: {list(d.keys())}")

# Check detail endpoint
if data:
    did = data[0]["id"]
    r2 = requests.get(f"{API}?action=detail&id={did}", timeout=10)
    det = r2.json().get("data", {})
    print(f"\n=== DETAIL for {data[0]['title']} ===")
    print(f"  genres: {det.get('genres', 'NOT FOUND')}")
    print(f"  genre: {det.get('genre', 'NOT FOUND')}")
    print(f"  category: {det.get('category', 'NOT FOUND')}")
    print(f"  tags: {det.get('tags', 'NOT FOUND')}")
    print(f"  all keys: {list(det.keys())}")
    
    # Print full detail as JSON for inspection
    safe = {k: v for k, v in det.items() if k != "episodes"}
    print(f"\n=== FULL DETAIL (no episodes) ===")
    print(json.dumps(safe, indent=2, ensure_ascii=False)[:2000])
