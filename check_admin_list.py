import requests

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

def list_admin_dramas():
    # Admin API for list often differs
    r = requests.get(f"{API_BASE}/api/admin/dramas?limit=20", headers=ADMIN_HDR, timeout=15)
    if r.ok:
        dramas = r.json()
        print(f"Admin Drama List (Total {len(dramas)}):")
        for d in dramas[:15]:
            print(f"- {d['title']} (ID: {d['id']})")
    else:
        print(f"Admin Error: {r.status_code} {r.text}")

if __name__ == "__main__":
    list_admin_dramas()
