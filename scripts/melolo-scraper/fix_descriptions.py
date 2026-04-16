import requests
import json

BASE_URL_PROXY = "https://vidrama.asia/api/netshort"
BACKEND_URL = "https://api.shortlovers.id/api"

# Get Admin Key from .env
import os
from dotenv import load_dotenv
load_dotenv()
ADMIN_KEY = os.getenv("ADMIN_API_KEY", "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14")

HEADERS = {
    "Authorization": f"Bearer {ADMIN_KEY}",
    "X-Admin-Key": ADMIN_KEY,
    "Content-Type": "application/json"
}

NETSHORT_IDS = [
    "2034157133506805762", # Satu Langkah Menjadi Dewa
    "2041056545151647745", # Legenda yang Terbuang
    "2037748734443388929"  # Raja Tinju di Balik Gerobak
]

for nid in NETSHORT_IDS:
    # 1. Get from Netshort
    api_url = f"{BASE_URL_PROXY}/api/drama/{nid}?lang=id_ID"
    r = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0", "Origin": "https://vidrama.asia", "Referer": "https://vidrama.asia/"})
    if r.status_code != 200:
        print(f"Failed to fetch {nid} from Netshort")
        continue
    
    data = r.json()
    detail = data.get("data", {})
    
    title = detail.get("shortPlayName") or detail.get("name") or ""
    desc = detail.get("shotIntroduce") or detail.get("introduce") or detail.get("description") or ""
    
    if not desc:
        print(f"No desc for {title}")
        continue
        
    slug = title.lower().replace(" ", "-")
    
    # 2. Search Backend
    sr = requests.get(f"{BACKEND_URL}/dramas/search_admin?q={title}", headers=HEADERS)
    if sr.status_code == 404 or sr.status_code != 200:
        # Try generic search
        sr = requests.get(f"{BACKEND_URL}/dramas", params={"search": title}, headers=HEADERS)
        if sr.status_code != 200:
            sr = requests.get(f"{BACKEND_URL}/dramas/search", params={"q": title}, headers=HEADERS)

    backend_id = None
    if sr.status_code == 200:
        try:
            dramas = sr.json()
            if isinstance(dramas, dict):
                dramas = dramas.get("dramas", [])
                
            for d in dramas:
                if d["title"].lower() == title.lower():
                    backend_id = d["id"]
                    break
        except:
            pass

    if not backend_id:
        print(f"Could not find backend ID for {title}")
        continue
        
    # 3. Patch backend
    pr = requests.patch(f"{BACKEND_URL}/dramas/{backend_id}", json={"description": desc}, headers=HEADERS)
    if pr.status_code == 200:
        print(f"Fixed Description for {title}")
    else:
        print(f"Failed to patch {title} - {pr.status_code} {pr.text}")
