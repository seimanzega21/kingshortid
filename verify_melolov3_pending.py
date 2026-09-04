import requests
import json

API_BASE = 'http://141.11.160.187:3000'

with open('melolov3_pending_queue.json', encoding='utf-8') as f:
    queue = json.load(f)

r = requests.get(f'{API_BASE}/api/dramas?limit=5000', timeout=60)
data = r.json()
all_dramas = data if isinstance(data, list) else data.get('dramas', [])
by_title = {d.get('title','').lower().strip(): d for d in all_dramas}

print("=" * 65)
print("VERIFICATION: 18 melolov3 pending dramas")
print("=" * 65)

ok = 0
incomplete = 0
not_found = 0

for q in queue:
    slug = q['slug']
    slug_words = slug.replace('-', ' ')

    found_drama = None
    for title_lower, d in by_title.items():
        if all(w in title_lower for w in slug_words.split() if len(w) > 3):
            found_drama = d
            break

    if not found_drama:
        print(f"[NOT FOUND] {slug}")
        not_found += 1
        continue

    drama_id = found_drama['id']
    title = found_drama['title']
    total_eps = found_drama.get('totalEpisodes', 0)

    r2 = requests.get(f'{API_BASE}/api/dramas/{drama_id}/episodes', timeout=15)
    actual = len(r2.json()) if r2.ok else 0

    if actual >= total_eps:
        print(f"[OK] {title} — {actual}/{total_eps} eps")
        ok += 1
    else:
        missing = list(set(range(1, total_eps+1)) - {int(e.get('episodeNumber',0)) for e in (r2.json() if r2.ok else [])})
        print(f"[INCOMPLETE] {title} — {actual}/{total_eps} eps | Missing: {sorted(missing)[:10]}{'...' if len(missing)>10 else ''}")
        incomplete += 1

print("\n" + "=" * 65)
print(f"SUMMARY: {ok} OK | {incomplete} incomplete | {not_found} not found")
print("=" * 65)
