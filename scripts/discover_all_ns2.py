import requests, urllib3, json
urllib3.disable_warnings()

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
}

def discover_all_ns2():
    # Try global search with provider filter
    url = "https://vidrama.asia/api/movie/global_list?lang=id_ID&page=1&limit=100&provider=netshortv2"
    r = requests.get(url, headers=WEB_HDRS, verify=False)
    if r.ok:
        data = r.json().get('data', {}).get('list', [])
        return data
    else:
        # Fallback: search keyword netshortv2
        url = "https://vidrama.asia/api/movie/global_list?lang=id_ID&page=1&limit=100&keyword=netshortv2"
        r = requests.get(url, headers=WEB_HDRS, verify=False)
        if r.ok:
            return r.json().get('data', {}).get('list', [])
    return []

dramas = discover_all_ns2()
print(f"Total drama ditemukan: {len(dramas)}")
for d in dramas[:20]:
    print(f" - {d.get('title')} (ID: {d.get('movieId')})")
