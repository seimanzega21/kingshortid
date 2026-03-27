"""Try FreeReels mobile API with VIP auth to get episode video UUIDs"""
import sys, requests, json, hashlib, hmac, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AUTH_KEY = '0mbsk7VVLt3JLNTqtC1EnJoK0pQAA3pW'
AUTH_SECRET = 'DjRzZ0PoETLc8K9nq1N89pX2dtvuspc3'
APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
FR_BASE = 'https://apiv2.free-reels.com/frv2-api'

# Generate auth signature
def make_sign(params: dict, secret: str) -> str:
    sorted_params = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
    return hmac.new(secret.encode(), sorted_params.encode(), hashlib.sha256).hexdigest()

ts = str(int(time.time()))

# Common headers for FreeReels API
def api_headers():
    return {
        'User-Agent': 'okhttp/4.9.3',
        'Content-Type': 'application/json',
        'auth-key': AUTH_KEY,
        'timestamp': ts,
        'version': '2.2.10',
        'platform': 'android',
        'Accept-Language': 'id',
    }

# Series key for "Lulus Masa Percobaan, Hamil oleh Bosku(Sulih Suara)"
SERIES_KEY = 'eNFDnztZRb'
EP_KEY = 'KhuqW30i3V'

api_tests = [
    f'/series/{SERIES_KEY}/episode/{EP_KEY}',
    f'/series/{SERIES_KEY}/episodes',
    f'/play/{SERIES_KEY}/{EP_KEY}',
    f'/v1/play?series={SERIES_KEY}&episode={EP_KEY}',
    f'/series/{SERIES_KEY}',
    f'/episode/{EP_KEY}/play',
]

print('=== FreeReels API Tests ===')
for path in api_tests:
    url = FR_BASE + path
    try:
        r = requests.get(url, headers=api_headers(), timeout=10)
        print(f'[{r.status_code}] {path}')
        if r.status_code == 200:
            try:
                data = r.json()
                print(f'  JSON keys: {list(data.keys())[:5]}')
                # Look for video URL
                raw = json.dumps(data)
                if '.m3u8' in raw or 'video-v' in raw or 'video_url' in raw.lower():
                    print(f'  *** VIDEO DATA FOUND! ***')
                    print(f'  {raw[:300]}')
            except:
                print(f'  Non-JSON: {r.text[:100]}')
    except Exception as e:
        print(f'Error {path}: {e}')
