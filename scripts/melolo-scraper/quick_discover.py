#!/usr/bin/env python3
"""Quick discovery with session + short timeouts."""
import requests, time, json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(line_buffering=True)

base = "https://vidrama.asia/api/melolo"
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json",
})

all_dramas = {}
keywords = ["a", "e", "i", "o", "u", "s", "k", "p", "d", "m"]

for kw in keywords:
    offset = 0
    while True:
        try:
            r = session.get(
                f"{base}?action=search&keyword={kw}&limit=50&offset={offset}",
                timeout=8
            )
            if r.status_code != 200:
                break
            items = r.json().get("data", [])
            if not items:
                break
            new = 0
            for item in items:
                did = item.get("id", "")
                if did and did not in all_dramas:
                    all_dramas[did] = item
                    new += 1
            if len(items) < 50:
                break
            offset += 50
            time.sleep(0.3)
        except Exception as e:
            err = str(e)[:50]
            print(f"  ERR {kw} offset={offset}: {err}", flush=True)
            break
    
    count = len(all_dramas)
    print(f"  '{kw}': {count} unique dramas", flush=True)
    time.sleep(0.3)

# Trending  
try:
    r = session.get(f"{base}?action=all-trending&limit=100", timeout=8)
    if r.status_code == 200:
        for item in r.json().get("data", []):
            did = item.get("id", "")
            if did and did not in all_dramas:
                all_dramas[did] = item
except:
    pass

drama_list = sorted(all_dramas.values(), key=lambda x: x["title"])
print(f"\nTotal: {len(drama_list)} dramas", flush=True)
for i, d in enumerate(drama_list, 1):
    t = d["title"]
    print(f"  {i:3}. {t}", flush=True)

with open("vidrama_all_dramas.json", "w", encoding="utf-8") as f:
    json.dump(drama_list, f, indent=2, ensure_ascii=False)
print(f"\nSaved: vidrama_all_dramas.json", flush=True)
