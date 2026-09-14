import json
from pathlib import Path
import requests, urllib3
urllib3.disable_warnings()

p_queue = Path("scripts/melolov3_queue.json")
with open(p_queue, "r", encoding="utf-8") as f:
    queue = json.load(f)

with open("scripts/batch_15_melolov3.json", "r", encoding="utf-8") as f:
    batch = json.load(f)

batch_map = {b["id"]: b for b in batch}

headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://vidrama.asia/"}
r = requests.get("https://vidrama.asia/api/melolov3/multi-video?id=7684141877947288581&lang=id", headers=headers, verify=False)
data = r.json()
pemburu = {
    "id": "7684141877947288581",
    "title": data.get("series", {}).get("title", "(Dub)Sang Legenda Pemburu"),
    "slug": "sang-legenda-pemburu",
    "totalEpisodes": data.get("series", {}).get("episode_count") or len(data.get("episodes", [])),
    "status": "pending"
}
batch_map["7684141877947288581"] = pemburu

items_order = [
    "7682646708114689077",
    "7673008968603585541",
    "7684141877947288581",
    "7679635530220325941",
    "7665941971797576709",
    "7684141877729168437",
    "7664445251251112965",
    "7677866737911499781",
    "7680466037560609797",
    "7683449646026345525",
    "7683449335295527989",
    "7680825016186850357",
    "7677866738842635269",
    "7681213242730908677",
    "7666276364357487669"
]

existing_ids = {item["id"] for item in queue}
added = 0
for mid in items_order:
    d = batch_map[mid]
    if d["id"] not in existing_ids:
        queue.append(d)
        added += 1
    else:
        for item in queue:
            if item["id"] == d["id"]:
                item["status"] = "pending"

with open(p_queue, "w", encoding="utf-8") as f:
    json.dump(queue, f, indent=2, ensure_ascii=False)

print("Total in queue:", len(queue), "newly added:", added)
for i, mid in enumerate(items_order, 1):
    d = batch_map[mid]
    print(f"{i}. {d['title']} ({d['totalEpisodes']} eps)")
