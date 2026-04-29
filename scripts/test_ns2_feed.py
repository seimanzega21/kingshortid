import requests, urllib3, json
urllib3.disable_warnings()

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
}

def check_feed():
    url = "https://vidrama.asia/api/netshortv2/feed/1?lang=id_ID"
    r = requests.get(url, headers=WEB_HDRS, verify=False)
    if r.ok:
        data = r.json().get('data', [])
        print(f"Found {len(data)} items in feed 1")
        for it in data[:5]:
            print(f" - {it.get('title')} (ID: {it.get('movieId')})")
    else:
        print(f"Error: {r.status_code}")

check_feed()
