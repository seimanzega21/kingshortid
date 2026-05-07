import requests, json, sys, os

API_BASE    = 'https://api.shortlovers.id'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

def check_drama():
    # Try searching for the drama
    r = requests.get(f"{API_BASE}/api/dramas?limit=100", timeout=15)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        target = next((d for d in dramas if 'Romantis di Musim Dingin' in d['title']), None)
        if target:
            print(f"FOUND DRAMA in DB: {target['title']} (ID: {target['id']})")
            return target['id']
        else:
            print(f"NOT FOUND in list. Response start: {str(data)[:200]}")
    
    # Try direct ID
    did = 'cxe8nonlnv3057higcrvddzg'
    r = requests.get(f"{API_BASE}/api/dramas/{did}", timeout=15)
    if r.ok:
        d = r.json()
        print(f"FOUND DRAMA by ID: {d['title']} (ID: {d['id']})")
        return d['id']
        
    print("Drama not found in DB")
    return None

if __name__ == "__main__":
    check_drama()
