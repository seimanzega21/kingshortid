"""Test H5 API endpoints for FreeReels drama info"""
import requests, hashlib, json, time

FR_BASE   = 'https://apiv2.free-reels.com/frv2-api'
FR_H5_BASE= 'https://apiv2.free-reels.com'
dh        = hashlib.md5(b'freereels_master_pipeline_v1').hexdigest()

sess = requests.Session()
sess.headers.update({
    'app-name': 'com.freereels.app', 'device': 'android',
    'app-version': '2.2.10', 'device-id': dh, 'device-hash': dh,
    'country': 'ID', 'language': 'id', 'shortcode': 'id',
    'User-Agent': 'okhttp/4.12.0',
})

APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
r = sess.post(f'{FR_BASE}/anonymous/login', json={'device_id': dh},
              headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
d = r.json().get('data', {})
ak  = d.get('auth_key', '')
ase = d.get('auth_secret', '')

def ah():
    sig = hashlib.md5(f'{APP_SECRET}&{ase}'.encode()).hexdigest()
    return {'authorization': f'oauth_signature={sig},oauth_token={ak},ts={int(time.time()*1000)}'}

test_ids = ['Cdg4Th1kpv', 'oMhM6vLVCs', '8hX52C1Do1']

# Try H5 API base URLs
h5_bases = [
    'https://apiv2.free-reels.com/h5-api',
    'https://m.mydramawave.com/h5-api',
    'https://api.mydramawave.com/h5-api',
    'https://apiv2.free-reels.com/frv2-api',   # standard
]

print('=== Testing h5-api/drama/info base URL variants ===')
for sid in test_ids[:2]:
    print(f'\n--- Series: {sid} ---')
    for base in h5_bases:
        url = f'{base}/drama/info'
        try:
            r = sess.get(url, headers=ah(), params={'series_id': sid}, timeout=8)
            print(f'  {base.split(".com/")[1] if ".com/" in base else base}: {r.status_code} len={len(r.text)} text={r.text[:60]}')
        except Exception as e:
            print(f'  {base}: ERROR {e}')
        time.sleep(0.2)
