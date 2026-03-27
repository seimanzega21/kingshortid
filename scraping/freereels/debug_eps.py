"""
Find episode list endpoint for FreeReels dramas
Tab 514 already has ep1 data - need to find how to get remaining episodes
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

# From fr_tab514_SUCCESS.json - first series
SERIES_KEY  = 'qQKGMS5WbW'   # series key from tab 514
EPISODE_KEY = 'JvVys2cBjA'   # episode key from tab 514 episode_info.id
SERIES_ID_NUM = 123569        # numeric series_id from r_info1

print('=== Testing episode list endpoints ===')
endpoints_to_try = [
    ('GET', f'{FR_BASE}/drama/episode_list', {'series_id': SERIES_KEY, 'page': 1, 'page_size': 20}),
    ('GET', f'{FR_BASE}/drama/episode_list', {'series_id': SERIES_ID_NUM, 'page': 1, 'page_size': 20}),
    ('GET', f'{FR_BASE}/drama/episode/list', {'series_id': SERIES_KEY}),
    ('GET', f'{FR_BASE}/drama/episodes', {'series_id': SERIES_KEY}),
    ('GET', f'{FR_BASE}/episode/list', {'series_id': SERIES_KEY, 'page': 1}),
    ('GET', f'{FR_BASE}/drama/episode/all', {'series_id': SERIES_KEY}),
    ('GET', f'{FR_BASE}/drama/detail', {'series_id': SERIES_KEY}),
    ('GET', f'{FR_BASE}/drama/info', {'series_id': SERIES_KEY}),
    ('GET', f'{FR_BASE}/drama/info', {'series_id': str(SERIES_ID_NUM)}),
    # Try POST
    ('POST', f'{FR_BASE}/drama/episode_list', {'series_id': SERIES_KEY, 'page': 1, 'page_size': 20}),
    ('POST', f'{FR_BASE}/drama/info', {'series_id': SERIES_KEY}),
]

for method, url, params in endpoints_to_try:
    try:
        if method == 'GET':
            r = sess.get(url, headers=ah(), params=params, timeout=8)
        else:
            r = sess.post(url, headers={**ah(), 'Content-Type': 'application/json', 'Skip-Encrypt': '1'},
                         json=params, timeout=8)
        ep = url.split('/frv2-api/')[1]
        decoded = dec(r.text)
        code = decoded.get('code', '?') if decoded else '?'
        print(f'  {method} {ep}({list(params.keys())[0]}={list(params.values())[0]}): {r.status_code} code={code} len={len(r.text)}')
        if r.status_code == 200 and decoded and decoded.get('code') in [0, 200]:
            print(f'   *** POTENTIAL HIT! Response: {str(decoded)[:200]}')
    except Exception as e:
        print(f'  ERROR: {e}')
    time.sleep(0.3)
