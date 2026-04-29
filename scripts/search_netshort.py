import requests, urllib3
urllib3.disable_warnings()

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
}

def search_netshort():
    url = "https://vidrama.asia/api/movie/global_list?lang=id_ID&page=1&limit=50&keyword=Netshort"
    r = requests.get(url, headers=WEB_HDRS, verify=False)
    if r.ok:
        data = r.json().get('data', {}).get('list', [])
        for it in data:
            print(f"Title: {it.get('title')} | ID: {it.get('movieId')} | Provider: {it.get('provider')}")
    else:
        print(f"Error: {r.status_code}")

search_netshort()
