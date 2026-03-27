"""Test FreeReels API directly with VIP auth credentials"""
import sys, requests, json, hashlib, time, hmac
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AUTH_KEY = '0mbsk7VVLt3JLNTqtC1EnJoK0pQAA3pW'
AUTH_SECRET = 'DjRzZ0PoETLc8K9nq1N89pX2dtvuspc3'
USER_ID = '36848605951'
APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'

# API base URLs to try
SERIES_KEY = 'eNFDnztZRb'
EP_KEY = 'KhuqW30i3V'

# Try various API endpoints
base_urls = [
    'https://apiv2.free-reels.com/frv2-api',
    'https://api.mydramawave.com',
    'https://apiv2.mydramawave.com',
]

headers = {
    'User-Agent': 'FreeReels/2.2.10 (Android)',
    'Content-Type': 'application/json',
    'auth-key': AUTH_KEY,
    'auth-secret': AUTH_SECRET,
    'X-Auth-Key': AUTH_KEY,
    'Authorization': f'Bearer {AUTH_KEY}',
}

ts = str(int(time.time()))

# Try to call episode video API
endpoints = [
    f'/series/{SERIES_KEY}/{EP_KEY}',
    f'/v1/series/{SERIES_KEY}/episodes/{EP_KEY}',
    f'/episode/video?series={SERIES_KEY}&episode={EP_KEY}',
    f'/v1/episode?key={EP_KEY}',
    f'/video?series_key={SERIES_KEY}&ep_key={EP_KEY}&auth_key={AUTH_KEY}',
]

for base in base_urls:
    for ep in endpoints[:2]:
        url = base + ep
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code < 500:
                print(f'OK [{r.status_code}]: {url}')
                if '.m3u8' in r.text or 'video' in r.text.lower():
                    print(f'  Response: {r.text[:300]}')
            else:
                print(f'[{r.status_code}]: {url}')
        except Exception as e:
            print(f'Error: {url} - {e}')
