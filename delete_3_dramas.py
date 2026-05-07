import requests

API_BASE = 'https://api.shortlovers.id'

def delete_drama(did):
    r = requests.delete(f"{API_BASE}/api/dramas/{did}")
    if r.ok:
        print(f"DELETED {did}")
    else:
        print(f"FAILED {did}: {r.status_code}")

if __name__ == "__main__":
    # IDs of the 3 dramas we just registered
    ids = [
        'a5t2801mi1n7ubbd5279wnab',
        'woxgf5gu2f97cs02mkmjhkln',
        'd40yxdr4m35sdkdrw6ezu64n'
    ]
    for did in ids:
        delete_drama(did)
    print("Cleanup done.")
