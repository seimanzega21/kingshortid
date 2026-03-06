import requests

BACKEND = "https://api.shortlovers.id/api"

# 1. Delete duplicate (0 eps)
dup_id = "vnutd1wnftai1ob4qltchqll"
print("[1/2] Deleting duplicate 'Aku Kaya Dari Giok' (0 eps)...", end="", flush=True)
r = requests.delete(f"{BACKEND}/dramas/{dup_id}", timeout=10)
if r.status_code == 200:
    print(f" ✅ {r.json().get('message','')}")
else:
    print(f" ❌ HTTP {r.status_code}: {r.text[:100]}")

# 2. Update original cover using PATCH by ID
orig_id = "cmleexmag00bchx5e1yt6lnfd"
new_cover = "https://stream.shortlovers.id/melolo/aku-kaya-dari-giok/cover.webp"
print("[2/2] Updating original 'Aku Kaya dari Giok' cover...", end="", flush=True)
r = requests.patch(f"{BACKEND}/dramas/{orig_id}", json={"cover": new_cover}, timeout=10)
if r.status_code == 200:
    print(f" ✅ Cover updated to .webp")
else:
    print(f" ❌ HTTP {r.status_code}: {r.text[:100]}")

# Verify
print("\nVerifying search 'aku kaya'...")
r = requests.get(f"{BACKEND}/dramas?limit=500", timeout=15)
all_d = r.json().get("dramas", [])
matches = [d for d in all_d if "aku kaya" in d.get("title","").lower() and "giok" in d.get("title","").lower()]
print(f"  Results: {len(matches)}")
for m in matches:
    print(f"  - '{m['title']}' | eps={m.get('totalEpisodes',0)} | cover=...{m.get('cover','')[-30:]}")
