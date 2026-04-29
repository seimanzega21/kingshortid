import requests, urllib3
urllib3.disable_warnings()

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
}

def get_all_netshortv2_dramas():
    dramas = []
    # Fetch first 2 pages to see what we have
    for page in range(1, 3):
        url = f"{VIDRAMA_API}/movie/list?page={page}&limit=50&lang=id_ID"
        r = requests.get(url, headers=WEB_HDRS, verify=False)
        if r.ok:
            items = r.json().get('data', {}).get('list', [])
            for it in items:
                dramas.append({
                    'title': it.get('title'),
                    'drama_id': it.get('movieId'),
                    'slug': it.get('movieId') # Use ID as slug fallback if needed
                })
        else:
            print(f"Error page {page}: {r.status_code}")
    return dramas

all_dramas = get_all_netshortv2_dramas()
print(f"Found {len(all_dramas)} dramas in NetshortV2 provider.")
for d in all_dramas[:10]:
    print(f" - {d['title']} ({d['drama_id']})")
