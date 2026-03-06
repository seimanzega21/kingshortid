"""Get 2 MicroDrama dramas with full detail including episodes and stream URLs."""
import requests
import json

API = "https://vidrama.asia/api/microdrama"

# 1. Get drama list
print("=== DRAMA LIST (first 2) ===")
r = requests.get(f"{API}?action=list&limit=2&offset=0", timeout=15)
data = r.json()
print(f"Total: {data.get('total', 0)} dramas")
dramas = data.get("dramas", [])

for i, d in enumerate(dramas):
    print(f"\n--- Drama {i+1} ---")
    print(json.dumps(d, indent=2, ensure_ascii=False)[:800])
    drama_id = d["id"]

    # 2. Get detail
    print(f"\n--- Detail for {drama_id} ---")
    dr = requests.get(f"{API}?action=detail&id={drama_id}", timeout=15)
    detail = dr.json()
    print(json.dumps(detail, indent=2, ensure_ascii=False)[:1500])

    # 3. Check episodes
    episodes = detail.get("episodes", detail.get("data", {}).get("episodes", []) if isinstance(detail.get("data"), dict) else [])
    if not episodes:
        # Try different key names
        for key in detail:
            val = detail[key]
            if isinstance(val, list) and len(val) > 0:
                print(f"\n  Found list key '{key}' with {len(val)} items")
                print(f"  Sample: {json.dumps(val[0], indent=2, ensure_ascii=False)[:300]}")

    # 4. Try stream
    print(f"\n--- Stream ep1 ---")
    for action in ["stream", "play", "episode", "watch"]:
        sr = requests.get(f"{API}?action={action}&id={drama_id}&episode=1", timeout=10)
        if sr.status_code == 200:
            sdata = sr.json()
            print(f"  action={action}: {json.dumps(sdata, indent=2, ensure_ascii=False)[:500]}")
            break
        else:
            print(f"  action={action}: {sr.status_code} {sr.text[:100]}")

    # 5. Try getting episodes list separately
    print(f"\n--- Episodes ---")
    for action in ["episodes", "episode-list"]:
        er = requests.get(f"{API}?action={action}&id={drama_id}", timeout=10)
        if er.status_code == 200:
            edata = er.json()
            print(f"  action={action}: {json.dumps(edata, indent=2, ensure_ascii=False)[:500]}")
            break
        else:
            print(f"  action={action}: {er.status_code} {er.text[:80]}")
