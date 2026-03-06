#!/usr/bin/env python3
"""Spot-check if partial dramas actually have episodes in Vidrama API"""
import requests, json, time, re

API_URL = "https://vidrama.asia/api/melolo"

with open("vidrama_all_dramas.json", "r", encoding="utf-8") as f:
    all_dramas = json.load(f)

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')

# Test dramas with known IDs from partial list
test_ids = [
    ("Antara Ambisi dan Cinta", "7594631535374912517"),
    ("Ayah Berandalan jadi CEO", "7543217293895928848"),
    ("Balas Dendam Sang Putri Genius", "7599511186308074501"),
    ("Dewa Balapan", "7584379137708526597"),
    ("Dokter Genius Pujaan Hati", "7462701593155079185"),
    ("Guru Kecil Genius", "7575423530993454133"),
    ("Identitas Rahasia Suamiku", "7582229626634636341"),
    ("Sang Dewa Judi", "7555717133372492853"),
]

# Find some no-ID dramas in discovery
no_id_slugs = ["800-ribu-beli-dunia-kultivasi", "ahli-pengobatan-sakti", "dewa-mahjong"]
for d in all_dramas:
    sl = slugify(d["title"])
    if sl in no_id_slugs:
        test_ids.append((d["title"], d["id"]))

print("=== SPOT-CHECKING VIDRAMA API ===")
print(f"Testing {len(test_ids)} dramas...\n")

has_eps = 0
no_eps = 0

for title, did in test_ids:
    try:
        r = requests.get(f"{API_URL}?action=detail&id={did}", timeout=10)
        if r.status_code == 200:
            detail = r.json().get("data", {})
            eps = detail.get("episodes", [])
            ep_count = len(eps)
            if ep_count > 0:
                first = eps[0].get("episodeNumber", "?")
                last = eps[-1].get("episodeNumber", "?")
                print(f"  {title}: {ep_count} eps (ep{first}-{last}) --> AVAILABLE")
                has_eps += 1
            else:
                print(f"  {title}: 0 eps --> NO EPISODES")
                no_eps += 1
        else:
            print(f"  {title}: API returned {r.status_code}")
            no_eps += 1
    except Exception as e:
        print(f"  {title}: Error - {e}")
        no_eps += 1
    time.sleep(0.5)

print(f"\nResult: {has_eps} have episodes, {no_eps} have no episodes")
print(f"Conclusion: {'Most partial dramas have episodes available for retry' if has_eps > no_eps else 'Many dramas have no episodes in API'}")
