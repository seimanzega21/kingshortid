"""
FreeReels - Smart Tab-Based Approach
Since drama/info = 404, use what works:
- Tab 514 gives ep1 HLS URL per drama
- Try drama episode list via watch_history or similar
- Try /drama/v2/episode_list with POST encrypted
"""
import requests, hashlib, json, time, base64, os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from pathlib import Path

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

def enc(d):
    p = json.dumps(d, separators=(',',':')).encode()
    pad = 16-(len(p)%16); p += bytes([pad]*pad)
    iv = os.urandom(16)
    c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
    e = c.encryptor()
    return base64.b64encode(iv+e.update(p)+e.finalize()).decode()

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

SERIES_KEY = 'qQKGMS5WbW'
SERIES_NUM = 123569

# Strategy: Try AES-encrypted POST to video/list or episode list
print('=== Testing AES-encrypted POST requests ===')
test_bodies = [
    {'series_id': SERIES_KEY, 'page': 1, 'page_size': 30},
    {'series_id': SERIES_KEY, 'episode_index': 2},
    {'series_key': SERIES_KEY, 'page': 1},
]

enc_endpoints = [
    f'{FR_BASE}/drama/episode_list',
    f'{FR_BASE}/drama/info',
    f'{FR_BASE}/drama/video_list',
]

for url in enc_endpoints:
    for body in test_bodies[:2]:
        enc_body = enc(body)
        r = sess.post(url, headers={**ah(), 'Content-Type': 'application/json'},
                     data=enc_body, timeout=8)
        ep = url.split('/frv2-api/')[1]
        decoded = dec(r.text)
        code = decoded.get('code','?') if decoded else '?'
        if r.status_code != 404:
            print(f'  HIT! {ep}: {r.status_code} code={code}')
            print(f'    {str(decoded)[:200] if decoded else r.text[:100]}')
        else:
            print(f'  404: {ep}')
        time.sleep(0.3)
