"""Test different drama info endpoints and find the working one"""
import requests, hashlib, json, time, base64, pathlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
AES_KEY    = b'2r36789f45q01ae5'
FR_BASE    = 'https://apiv2.free-reels.com/frv2-api'
dh         = hashlib.md5(b'freereels_master_pipeline_v1').hexdigest()

sess = requests.Session()
sess.headers.update({
    'app-name': 'com.freereels.app', 'device': 'android',
    'app-version': '2.2.10', 'device-id': dh, 'device-hash': dh,
    'country': 'ID', 'language': 'id', 'shortcode': 'id',
    'User-Agent': 'okhttp/4.12.0',
})

r = sess.post(f'{FR_BASE}/anonymous/login', json={'device_id': dh},
              headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
d = r.json().get('data', {})
ak  = d.get('auth_key', '')
ase = d.get('auth_secret', '')
print(f'Login: ak={ak[:10]}...')

def ah():
    sig = hashlib.md5(f'{APP_SECRET}&{ase}'.encode()).hexdigest()
    return {'authorization': f'oauth_signature={sig},oauth_token={ak},ts={int(time.time()*1000)}'}

def dec(t):
    try:
        rb = base64.b64decode(t)
        iv, ct = rb[:16], rb[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct) + c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(t)
        except: return None

# Known working series_id from past scrape
WORKING_SID = 'Cdg4Th1kpv'  # Bertahan Hidup di Sekolah Elite
TAB514_SID  = 'oMhM6vLVCs'  # From tab 514 feed

# Test multiple endpoint variants
endpoints = [
    f'{FR_BASE}/drama/info',
    f'{FR_BASE}/drama/v2/info',
    f'{FR_BASE}/series/info',
    f'{FR_BASE}/series/detail',
    f'{FR_BASE}/drama/detail',
    f'{FR_BASE}/v2/drama/info',
]

print('\n=== Testing with WORKING ID (Cdg4Th1kpv) ===')
for ep in endpoints:
    r = sess.get(ep, headers=ah(), params={'series_id': WORKING_SID}, timeout=10)
    decoded = dec(r.text)
    code = decoded.get('code', '?') if decoded else '?'
    print(f'  {ep.split("/frv2-api/")[1]}: status={r.status_code} code={code} len={len(r.text)}')
    time.sleep(0.3)

print('\n=== Testing with TAB514 ID (oMhM6vLVCs) - different params ===')
params_variants = [
    {'series_id': TAB514_SID},
    {'key': TAB514_SID},
    {'id': TAB514_SID},
    {'drama_id': TAB514_SID},
]
for params in params_variants:
    r = sess.get(f'{FR_BASE}/drama/info', headers=ah(), params=params, timeout=10)
    decoded = dec(r.text)
    code = decoded.get('code', '?') if decoded else '?'
    print(f'  params={params}: status={r.status_code} code={code}')
    time.sleep(0.3)

# Also try tab 514 detailed fetch to see if there's a drama_id field
print('\n=== Full tab 514 item fields ===')
r = sess.post(f'{FR_BASE}/homepage/v2/tab/feed',
              json={'tab_key':'514','module_key':'514','page':1,'page_size':3},
              headers={**ah(),'Content-Type':'application/json','Skip-Encrypt':'1'}, timeout=15)
resp = r.json() if r.ok else {}
items = resp.get('data', {}).get('items') or resp.get('data', {}).get('list', [])
if items:
    print(f'Keys in item: {list(items[0].keys())}')
