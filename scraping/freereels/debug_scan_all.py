"""
FreeReels - Find working endpoints by trying all known variants
Using numeric series ID from r_info1 data
"""
import requests, hashlib, json, time, base64
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
ak, ase = d.get('auth_key', ''), d.get('auth_secret', '')

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

# From r_info1: series_id=123569, series_key=qQKGMS5WbW
SERIES_KEY = 'qQKGMS5WbW'
SERIES_NUM = 123569

# Comprehensive endpoint test
print('=== Comprehensive API scan ===')
all_endpoints = [
    ('GET',  f'{FR_BASE}/drama/v2/info',           {'series_id': SERIES_KEY}),
    ('GET',  f'{FR_BASE}/drama/v3/info',           {'series_id': SERIES_KEY}),
    ('GET',  f'{FR_BASE}/series/info',             {'series_id': SERIES_KEY}),
    ('GET',  f'{FR_BASE}/series/episode_list',     {'series_id': SERIES_KEY, 'page': 1}),
    ('GET',  f'{FR_BASE}/drama/ep/list',           {'series_id': SERIES_KEY}),
    ('POST', f'{FR_BASE}/drama/episode_list',      {'series_id': SERIES_KEY, 'page': 1, 'page_size': 20}),
    ('POST', f'{FR_BASE}/drama/ep_list',           {'series_id': SERIES_KEY, 'page': 1}),
    ('GET',  f'{FR_BASE}/drama/info',              {'key': SERIES_KEY}),
    # numeric ID variants
    ('GET',  f'{FR_BASE}/drama/info',              {'series_id': SERIES_NUM}),
    ('GET',  f'{FR_BASE}/drama/episode_list',      {'series_id': SERIES_NUM, 'page': 1}),
    # Try video endpoint
    ('GET',  f'{FR_BASE}/drama/video_list',        {'series_id': SERIES_KEY}),
    ('GET',  f'{FR_BASE}/drama/video/list',        {'series_id': SERIES_KEY, 'page': 1}),
    # discover
    ('GET',  f'{FR_BASE}/user/series/list',        {}),
    ('GET',  f'{FR_BASE}/drama/list',              {'tab': '514', 'page': 1}),
]

for method, url, params in all_endpoints:
    try:
        if method == 'GET':
            r = sess.get(url, headers=ah(), params=params, timeout=8)
        else:
            r = sess.post(url, headers={**ah(),'Content-Type':'application/json','Skip-Encrypt':'1'},
                         json=params, timeout=8)
        ep = url.split('/frv2-api/')[1] if '/frv2-api/' in url else url
        if r.status_code != 404:
            decoded = dec(r.text)
            code = decoded.get('code', '?') if decoded else '?'
            print(f'  HIT! {method} {ep}: status={r.status_code} code={code} len={len(r.text)}')
            print(f'    Content: {str(decoded)[:300] if decoded else r.text[:150]}')
        else:
            ep = url.split('/frv2-api/')[1] if '/frv2-api/' in url else url
            print(f'  404: {method} {ep}')
    except Exception as e:
        print(f'  ERR: {e}')
    time.sleep(0.3)
