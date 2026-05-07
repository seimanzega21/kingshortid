import requests

API_BASE = 'https://api.shortlovers.id'

def check_visibility():
    ids = ['cmlyu7p1q0001uxfx7dt279tt', 'cmlyu8p1r0002uxfx8dt279tt', 'cmlyu9p1s0003uxfx9dt279tt']
    for did in ids:
        r = requests.get(f"{API_BASE}/api/dramas/{did}?includeInactive=true", timeout=15)
        if r.ok:
            d = r.json()
            eps_count = len(d.get('episodes', []))
            print(f"DRAMA: {d['title']}")
            print(f"  ID: {d['id']}")
            print(f"  Status Active: {d.get('isActive')}")
            print(f"  Episodes in DB: {eps_count}")
            print("-" * 30)
        else:
            print(f"ID {did} not found: {r.status_code}")

if __name__ == "__main__":
    check_visibility()
