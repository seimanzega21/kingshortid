#!/usr/bin/env python3
"""Cross-check DB dramas vs R2 episode storage."""
import requests, json

BACKEND = "http://localhost:3001/api"

# 1. Get all dramas from DB
print("--- FETCHING DB DRAMAS ---")
r = requests.get(f"{BACKEND}/dramas?limit=500", timeout=10)
data = r.json()
items = data if isinstance(data, list) else data.get("dramas", [])
print(f"Total in DB: {len(items)}")

# 2. Check each drama for episodes using correct endpoint
no_eps = []
has_eps = []
errors = []
for i, d in enumerate(items, 1):
    did = d["id"]
    title = d["title"]
    try:
        url = f"{BACKEND}/dramas/{did}/episodes"
        er = requests.get(url, timeout=5)
        if er.status_code == 200:
            eps = er.json()
            if isinstance(eps, dict):
                eps = eps.get("episodes", [])
            ep_count = len(eps) if isinstance(eps, list) else 0
        else:
            ep_count = 0
            errors.append(f"{title}: HTTP {er.status_code}")
    except Exception as ex:
        ep_count = -1
        errors.append(f"{title}: {ex}")

    if ep_count <= 0:
        no_eps.append((title, d.get("provider", ""), d.get("totalEpisodes", 0)))
    else:
        has_eps.append((title, ep_count, d.get("totalEpisodes", 0)))

    if i % 20 == 0:
        print(f"  [{i}/{len(items)}] checked...")

# 3. Report
print(f"\n{'='*60}")
print(f"  DB EPISODE STATUS")
print(f"{'='*60}")
print(f"  With episodes:    {len(has_eps)}")
print(f"  Without episodes: {len(no_eps)}")
if errors:
    print(f"  Errors:           {len(errors)}")

if no_eps:
    print(f"\n{'─'*60}")
    print(f"  DRAMAS WITHOUT EPISODES IN DB ({len(no_eps)})")
    print(f"{'─'*60}")
    for title, provider, total in sorted(no_eps):
        extra = f" [expected {total}]" if total > 0 else ""
        print(f"  ❌ {title}{extra}")

print(f"\n{'─'*60}")
print(f"  DRAMAS WITH EPISODES ({len(has_eps)})")
print(f"{'─'*60}")
for title, count, total in sorted(has_eps):
    match = "✅" if total == 0 or count >= total else f"⚠️ ({count}/{total})"
    print(f"  {match} {title}: {count} eps")
