import requests

API_BASE = 'http://141.11.160.187:3000'
ADMIN_HDR = {'x-admin-key': '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'}

# Drama IDs from the patch log
to_delete = [
    ('ps4gbr0cqg0jxuv75na0td0e', 'Jerat Terlarang Sang Profesor'),
    ('m0hmvycuh33770mggt0tmsbc', 'Legenda Sang Raja Perang'),
]

for drama_id, title in to_delete:
    print(f"Deleting: {title} (ID: {drama_id})")
    r = requests.delete(f"{API_BASE}/api/admin/dramas/{drama_id}", headers=ADMIN_HDR, timeout=15)
    if r.ok:
        print(f"  DELETED successfully")
    else:
        print(f"  FAILED: {r.status_code} {r.text[:100]}")
        # Try alternative endpoint
        r2 = requests.delete(f"{API_BASE}/api/dramas/{drama_id}", headers=ADMIN_HDR, timeout=15)
        print(f"  Alt endpoint: {r2.status_code} {r2.text[:100]}")

print("Done.")
