# -*- coding: utf-8 -*-
import json
import requests
import urllib3

urllib3.disable_warnings()

api_base = 'https://api.shortlovers.id/api'
catalog_path = "d:/kingshortid/scratch/dramawave_catalog.json"

def check_duplicate_in_db(title):
    try:
        r = requests.get(f"{api_base}/dramas/search?q={title}", timeout=10)
        if r.ok:
            dramas = r.json().get('dramas', [])
            for d in dramas:
                if d['title'].lower().strip() == title.lower().strip():
                    return d['id']
    except Exception as e:
        pass
    return None

try:
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)
except Exception as e:
    print(f"Error loading catalog: {e}")
    catalog = []

print(f"Total dramas in catalog: {len(catalog)}")
scraped_dramas = []

for idx, d in enumerate(catalog):
    title = d.get("title")
    movie_id = d.get("id")
    db_id = check_duplicate_in_db(title)
    if db_id:
        # Get episode count
        ep_count = 0
        try:
            r_eps = requests.get(f"{api_base}/dramas/{db_id}/episodes")
            if r_eps.ok:
                ep_count = len(r_eps.json())
        except:
            pass
        scraped_dramas.append({
            "id": movie_id,
            "title": title,
            "db_id": db_id,
            "episodes": ep_count
        })

print(f"\nTotal DramaWave dramas found in Database: {len(scraped_dramas)}")
for idx, d in enumerate(scraped_dramas):
    print(f"{idx+1:02d}. Title: {d['title']} | Drama ID: {d['db_id']} | Provider ID: {d['id']} | Episodes in DB: {d['episodes']}")
