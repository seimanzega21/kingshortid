import requests

BACKEND_URL = "https://api.shortlovers.id/api"

def fix_active_status():
    print("Fetching newest dramas...")
    resp = requests.get(f"{BACKEND_URL}/dramas/new?limit=20")
    dramas = resp.json()
    
    count = 0
    for d in dramas:
        id = d["id"]
        title = d.get("title", "")
        # The newest dramas that have 1 episode or are Netshort titles
        if "Gejolak" in title or "Kaisar" in title or d.get("totalEpisodes", 0) <= 1:
            print(f"Patching {id} ({title}) to False...")
            requests.patch(f"{BACKEND_URL}/dramas/{id}", json={"isActive": False})
            count += 1
            
    print(f"Fixed {count} dramas!")

if __name__ == "__main__":
    fix_active_status()
