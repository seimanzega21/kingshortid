import requests
import json

API_BASE = "https://api.shortlovers.id/api"
ADMIN_KEY = "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"
ADMIN_HDR = {"x-admin-key": ADMIN_KEY, "Content-Type": "application/json"}

def list_dramas():
    r = requests.get(f"{API_BASE}/dramas?limit=500&includeInactive=true", headers=ADMIN_HDR)
    if r.ok:
        dramas = r.json()
        if isinstance(dramas, dict):
            dramas = dramas.get("dramas", [])
        
        print(f"Total dramas in DB: {len(dramas)}")
        dramabox_dramas = []
        for d in dramas:
            desc = d.get("description", "")
            cover = d.get("cover", "")
            title = d.get("title", "")
            
            # Check if dramabox
            is_db = False
            book_id = None
            
            # Try to extract book_id from description or URL
            m = re.search(r'BookID:\s*(\d+)', desc, re.IGNORECASE)
            if m:
                book_id = m.group(1)
                is_db = True
                
            if "dramabox" in cover or "dramabox" in desc.lower() or "dramabox" in str(d.get("tagList", [])).lower():
                is_db = True
                
            if is_db or "Mendengar" in title:
                dramabox_dramas.append({
                    "id": d["id"],
                    "title": title,
                    "book_id": book_id,
                    "cover": cover
                })
                
        print(f"Found {len(dramabox_dramas)} potential Dramabox dramas:")
        for dd in dramabox_dramas:
            print(f"  - {dd['title']} (ID: {dd['id']}, BookID: {dd['book_id']})")
            
import re
if __name__ == "__main__":
    list_dramas()
