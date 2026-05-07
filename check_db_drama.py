import requests, json, sys, os

API_BASE    = 'https://api.shortlovers.id'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

def check_drama():
    did = 'cxe8nonlnv3057higcrvddzg'
    r = requests.get(f"{API_BASE}/api/dramas/{did}", timeout=15)
    if r.ok:
        d = r.json()
        print(f"FOUND DRAMA by ID: {d['title']} (ID: {d['id']})")
        return d['id']
    else:
        print(f"Error fetching drama by ID: {r.status_code} {r.text}")
        
    # Search by title
    r = requests.get(f"{API_BASE}/api/dramas?search=Romantis%20di%20Musim%20Dingin", timeout=15)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        if dramas:
            print(f"FOUND DRAMA by SEARCH: {dramas[0]['title']} (ID: {dramas[0]['id']})")
            return dramas[0]['id']

    print("Drama not found in DB")
    return None

if __name__ == "__main__":
    check_drama()
