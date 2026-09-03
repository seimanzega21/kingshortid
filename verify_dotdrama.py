"""
Verify all dramas from dotdrama batch queue against KingShort DB.
Checks episode count per drama and reports any gaps.
"""
import requests
import json

API_BASE = 'http://141.11.160.187:3000'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY}

# All dotdrama dramas we ingested (including the 3 before the batch)
EXPECTED_DRAMAS = [
    {"title": "Aku Cerai dari Sang Miliarder (Sulih Suara)", "total": 50},
    {"title": "Ratu Hilang, Raja Naga Gelisah", "total": 40},
    {"title": "Gema Malam: Kembalinya Sang Ratu (Sulih Suara)", "total": 60},
]

# Add the 20 from the queue
with open('dotdrama_queue.json', 'r', encoding='utf-8') as f:
    queue = json.load(f)
for q in queue:
    EXPECTED_DRAMAS.append({"title": q["title"], "total": None})  # total unknown, will get from API

def get_all_db_dramas():
    r = requests.get(f"{API_BASE}/api/dramas?limit=5000", timeout=30)
    data = r.json()
    dramas = data if isinstance(data, list) else data.get('dramas', [])
    return {d['title'].strip().lower(): d for d in dramas}

def check_drama(db_drama):
    drama_id = db_drama['id']
    title = db_drama['title']
    expected_total = db_drama.get('totalEpisodes', 0)

    r = requests.get(f"{API_BASE}/api/dramas/{drama_id}/episodes", timeout=20)
    if not r.ok:
        return {"title": title, "status": "ERROR", "expected": expected_total, "found": 0, "missing": []}

    episodes = r.json()
    found_numbers = sorted([int(ep.get('episodeNumber', 0)) for ep in episodes if ep.get('episodeNumber')])

    expected_range = list(range(1, expected_total + 1))
    missing = [n for n in expected_range if n not in found_numbers]

    return {
        "title": title,
        "status": "OK" if not missing else "INCOMPLETE",
        "expected": expected_total,
        "found": len(found_numbers),
        "missing": missing
    }

def main():
    print("=" * 70)
    print("EPISODE VERIFICATION FOR ALL DOTDRAMA INGESTIONS")
    print("=" * 70)

    all_db = get_all_db_dramas()
    print(f"Total dramas in DB: {len(all_db)}\n")

    results = []
    titles_to_check = [d["title"].strip().lower() for d in EXPECTED_DRAMAS]

    not_found = []
    for d in EXPECTED_DRAMAS:
        t = d["title"].strip().lower()
        if t not in all_db:
            not_found.append(d["title"])

    if not_found:
        print("NOT FOUND IN DB:")
        for t in not_found:
            print(f"  - {t}")

    print("\nChecking episode counts...\n")
    checked = 0
    for d in EXPECTED_DRAMAS:
        t = d["title"].strip().lower()
        if t not in all_db:
            continue
        db_drama = all_db[t]
        result = check_drama(db_drama)
        results.append(result)
        status_icon = "OK" if result["status"] == "OK" else "INCOMPLETE"
        print(f"[{status_icon}] {result['title']}")
        print(f"       Expected: {result['expected']}  |  Found in DB: {result['found']}", end="")
        if result["missing"]:
            print(f"  |  Missing eps: {result['missing']}")
        else:
            print()
        checked += 1

    print("\n" + "=" * 70)
    ok = sum(1 for r in results if r["status"] == "OK")
    incomplete = sum(1 for r in results if r["status"] == "INCOMPLETE")
    print(f"SUMMARY: {ok} complete | {incomplete} incomplete | {len(not_found)} not found in DB")
    print("=" * 70)

    if incomplete > 0:
        print("\nINCOMPLETE DRAMAS NEEDING PATCH:")
        for r in results:
            if r["status"] == "INCOMPLETE":
                print(f"  - {r['title']} | Missing: {r['missing']}")

if __name__ == '__main__':
    main()
