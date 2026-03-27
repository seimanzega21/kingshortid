"""Debug FreeReels drama/info endpoint"""
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

# Login anonymous
r = sess.post(f'{FR_BASE}/anonymous/login', json={'device_id': dh},
              headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
d = r.json().get('data', {})
ak  = d.get('auth_key', '')
ase = d.get('auth_secret', '')
print(f'Auth key={ak[:10]}... secret={ase[:10]}...')

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

# Load series IDs
series = json.loads(pathlib.Path('freereels_series_ids.json').read_text(encoding='utf-8'))
test_ids = list(series.keys())[:5]

for test_id in test_ids:
    print(f'\n--- Testing series ID: {test_id} ---')
    r = sess.get(f'{FR_BASE}/drama/info', headers=ah(),
                 params={'series_id': test_id}, timeout=20)
    print(f'Status: {r.status_code}')
    print(f'Raw (200 chars): {r.text[:200]}')
    decoded = dec(r.text)
    if decoded:
        code = decoded.get('code')
        msg  = decoded.get('message', '')
        data = decoded.get('data', {})
        info = data.get('info', data) if isinstance(data, dict) else {}
        name = info.get('name', '?') if isinstance(info, dict) else '?'
        eps  = len(info.get('episode_list', [])) if isinstance(info, dict) else 0
        print(f'Code={code} msg={msg} name={name} eps={eps}')
    else:
        print('FAILED TO DECODE')
    time.sleep(0.5)
