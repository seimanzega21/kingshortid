# -*- coding: utf-8 -*-
import requests
import json
import urllib3
import time

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36',
    'Referer': 'https://vidrama.asia/watch/penyembuhnya-istrinya--ahTFgKtAU6/1?provider=dramawave&lang=id-ID',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; cf_clearance=J8QFuJs0er_WIP38vGy8bjQfQaQL7sFTKyEKgGeK3VA-1780795517-1.2.1.1-Obw73xI.dqmiSQdVtDuHFyZsbOD__sHZFc41Z7WuSJ_1XtPMHcVP7WGAmZM8UgRkfx1RmvPS8Mw6RV1Mxfy8nk9u5mLxnsCPd5XkJDAuQt5e1ZGXCvwfimrkbxXEBc0HLaV.tjy8GFC4chNPLXWwIu4XnAHluPvijjp6AziSEihvKlcO8S0gch2..hjZ.VvlLPFiQbKEWQd199XmWcHUjSlN1UbWgD9KtCXDZbIrrDBBDMAs874kQ6SiYfvaMVnn6MnmPE8TK1BVmFSj7tZDw.BioSjkB.O90BCUGYiLXLNnyCCnQCK4EiOE3hE7YmiOB08mCTr7Kh7ZZrGjyJQQaA; HstCnv5004644=64; HstCns5004644=86; panoramaId_expiry=1780881920064; HstCla5004644=1780795871370; HstPn5004644=2; HstPt5004644=159; ttcsid=1780795518124::qxBtmNAk35AwC3LWSvED.147.1780796502041.0::1.983569.353633::983547.23.360.812::604689.184.0; ttcsid_D5SNQPRC77UDQTF8A5EG=1780795518124::Zbl64-bTTugcPcmu7xs9.128.1780796502041.1; _ga_HCQQPKGEVH=GS2.1.s1780795517$o130$g1$t1780796502$j60$l0$h0'
}

api_base = 'https://api.shortlovers.id/api'

def check_duplicate_in_db(title):
    try:
        r = requests.get(f"{api_base}/dramas/search?q={title}", timeout=10)
        dramas = r.json().get('dramas', [])
        for d in dramas:
            if d['title'].lower().strip() == title.lower().strip():
                return d['id']
    except Exception as e:
        pass
    return None

all_dramas = []
seen_ids = set()

# We only fetch pages 1 to 3 to keep it bounded and fast (approx. 320 dramas)
max_pages = 3

for page in range(1, max_pages + 1):
    url = f"https://vidrama.asia/api/dramawave?action=list&page={page}"
    print(f"Fetching page {page}...", flush=True)
    try:
        r = requests.get(url, headers=headers, timeout=15, verify=False)
        if not r.ok:
            print(f"Error status code: {r.status_code}", flush=True)
            break
        data = r.json()
        if not data.get("success"):
            print("API returned success=false", flush=True)
            break
        drama_list = data.get("data", {}).get("dataList", [])
        if not drama_list:
            print("No more dramas in list", flush=True)
            break
            
        print(f"Page {page} returned {len(drama_list)} dramas. Checking database...", flush=True)
        for idx, d in enumerate(drama_list):
            sp_id = d.get("shortPlayId")
            name = d.get("shortPlayName")
            if sp_id and sp_id not in seen_ids:
                seen_ids.add(sp_id)
                db_id = check_duplicate_in_db(name)
                all_dramas.append({
                    "id": sp_id,
                    "title": name,
                    "exists_in_db": db_id
                })
        
        has_more = data.get("data", {}).get("hasMore", False)
        if not has_more:
            break
        time.sleep(1)
    except Exception as e:
        print("Exception:", e, flush=True)
        break

print(f"\nDiscovered {len(all_dramas)} unique dramas from pages 1-{max_pages}:", flush=True)
new_count = 0
for idx, d in enumerate(all_dramas):
    status = f"Exists in DB (ID: {d['exists_in_db']})" if d['exists_in_db'] else "NEW"
    if not d['exists_in_db']:
        new_count += 1
    print(f"{idx+1:02d}. ID: {d['id']} | Title: {d['title']} | Status: {status}", flush=True)

print(f"\nTotal new dramas discovered: {new_count}", flush=True)

# Save the list to a JSON file
with open("d:/kingshortid/scratch/dramawave_catalog.json", "w", encoding="utf-8") as f:
    json.dump(all_dramas, f, indent=2, ensure_ascii=False)
