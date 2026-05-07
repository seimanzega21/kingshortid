import requests

API_BASE = 'https://api.shortlovers.id'
DRAMA_ID = 'cxe8nonlnv3057higcrvddzg'

def verify():
    r = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID}?includeInactive=true", timeout=15)
    if r.ok:
        data = r.json()
        episodes = data.get('episodes', [])
        ep32 = next((ep for ep in episodes if ep.get('episodeNumber') == 32), None)
        if ep32:
            print(f"VERIFIED: Episode 32 exists in DB!")
            print(f"Video URL: {ep32.get('videoUrl')}")
        else:
            print("FAILED: Episode 32 not found in DB")
    else:
        print(f"Error: {r.status_code}")

if __name__ == "__main__":
    verify()
