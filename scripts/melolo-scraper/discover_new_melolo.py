#!/usr/bin/env python3
"""
Sample melolo API to find new Indonesian dramas not yet in R2.
Uses search keywords to discover undiscovered dramas.
"""
import requests, sys, json, re, boto3, os
from dotenv import load_dotenv
load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

API_URL = "https://vidrama.asia/api/melolo"

# === Read existing R2 slugs ===
def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

s3 = boto3.client("s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto",
)
paginator = s3.get_paginator("list_objects_v2")
r2_slugs = set()
for prefix in ["melolo/", "dramas/melolo/"]:
    for page in paginator.paginate(Bucket="shortlovers", Prefix=prefix, Delimiter="/"):
        for p in page.get("CommonPrefixes", []):
            slug = p["Prefix"].rstrip("/").split("/")[-1]
            if slug:
                r2_slugs.add(slug)
print(f"R2 existing slugs: {len(r2_slugs)}")

# === Search with many keywords ===
keywords = [
    "sang", "cinta", "hati", "takdir", "naga", "dokter", "raja", "ratu",
    "putri", "pangeran", "istri", "suami", "ibu", "ayah", "anak", "keluarga",
    "bangkit", "dendam", "rahasia", "musuh", "sahabat", "istana", "kerajaan",
    "penguasa", "penakluk", "tabib", "kultivator", "kasih", "jiwa",
    "lahir", "kembali", "menikah", "cerai", "mafia", "desa", "dunia",
    "adik", "kakak", "saudari", "pendekar", "langit", "harimau",
    "terjatuh", "terjebak", "terbuang", "tersembunyi", "terperangkap",
    "nasib", "pembalas", "pembalasan", "penyelamat", "kaya", "miskin",
]

seen_ids = set()
new_dramas = []

for kw in keywords:
    page = 0
    while True:
        try:
            r = requests.get(f"{API_URL}?action=search&keyword={kw}&limit=50&offset={page*50}", timeout=15)
            if r.status_code != 200:
                break
            data = r.json()
            items = data.get("data", [])
            if not items:
                break
            added = 0
            for d in items:
                did = d.get("id", "")
                if did in seen_ids:
                    continue
                seen_ids.add(did)
                slug = slugify(d.get("title", ""))
                if slug not in r2_slugs:
                    new_dramas.append(d)
                    added += 1
            if not data.get("hasMore"):
                break
            page += 1
        except Exception as e:
            print(f"  {kw} error: {e}")
            break

print(f"\nNew (not in R2) melolo dramas found: {len(new_dramas)}")
print()
for i, d in enumerate(new_dramas[:50], 1):
    eps = d.get("totalEpisodes", "?")
    print(f"{i:3}. {d['title']} ({eps} eps)")

with open("melolo_new_dramas.json", "w", encoding="utf-8") as f:
    json.dump(new_dramas, f, indent=2, ensure_ascii=False)
print(f"\nSaved {len(new_dramas)} dramas to melolo_new_dramas.json")
