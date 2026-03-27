"""
FreeReels scraper - Tab-based approach
Since drama/info is dead, use episode pagination directly
- Tab 514 gives episode 1 for each drama
- /drama/episode_list might work with numeric series_id
Try to find episode list endpoint
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
print(f'Login OK ak={ak[:10]}...')

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

# Data from fr_tab514_SUCCESS.json r_info1
series_key  = 'qQKGMS5WbW'
series_id_n = 123569   # numeric from r_info1.series_id
ep_key      = 'JvVys2cBjA'

# Test drama/detail more carefully
print('\n=== Testing drama/detail ===')
r = sess.get(f'{FR_BASE}/drama/detail', headers=ah(),
             params={'series_id': series_key}, timeout=10)
print(f'Status: {r.status_code}, len={len(r.text)}')
decoded = dec(r.text)
if decoded:
    print(f'Decoded keys: {list(decoded.keys()) if isinstance(decoded, dict) else type(decoded)}')
    print(f'Content: {str(decoded)[:400]}')
else:
    print(f'Raw: {r.text[:300]}')

print()

# Test episode pagination - maybe we paginate from episode ID
episode_endpoints = [
    f'{FR_BASE}/drama/episode_list',
    f'{FR_BASE}/drama/episodes',  
    f'{FR_BASE}/episode/list',
    f'{FR_BASE}/drama/v2/episode_list',
]

for ep_url in episode_endpoints:
    # Try numeric series ID
    for sid in [series_key, str(series_id_n), series_id_n]:
        r = sess.get(ep_url, headers=ah(),
                     params={'series_id': sid, 'page': 1, 'page_size': 20}, timeout=8)
        decoded = dec(r.text)
        code = decoded.get('code', '?') if decoded else '?'
        ep_name = ep_url.split('/frv2-api/')[1]
        if r.status_code != 404:
            print(f'  {ep_name} (sid={sid}): status={r.status_code} code={code}')
            print(f'    Content: {str(decoded)[:200] if decoded else r.text[:100]}')
        time.sleep(0.2)
