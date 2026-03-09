"""
Test drama/view API with valid ALPHANUMERIC series_id from browser intercept.
series_id format: alphanumeric string like 'Cdg4Th1kpv'
"""
import sys, json, time, base64, hashlib, os, re
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AES_KEY = b'2r36789f45q01ae5'; APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
BASE_DW = 'https://api.mydramawave.com/h5-api'
BASE_FR = 'https://apiv2.free-reels.com/frv2-api'

def dec(t):
    try:
        r = base64.b64decode(t); iv, ct = r[:16], r[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct) + c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(t)
        except: return None

def enc(data):
    payload = json.dumps(data, separators=(',', ':')).encode()
    pad = 16 - (len(payload) % 16); payload += bytes([pad] * pad)
    iv = os.urandom(16)
    c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
    e = c.encryptor(); return base64.b64encode(iv + e.update(payload) + e.finalize()).decode()

# Valid alphanumeric series IDs from browser intercept
VALID_IDS = ['Cdg4Th1kpv', '8hX52C1Do1']

dh = hashlib.md5(b'freereels_scraper_v1_kingshortid').hexdigest()

# ── DramaWave ────────────────────────────────────────────────────────────────
dw = requests.Session()
dw.headers.update({'app-name': 'com.dramawave.h5', 'device': 'h5', 'app-version': '1.2.20',
                   'device-id': dh, 'device-hash': dh, 'country': 'ID', 'language': 'id',
                   'shortcode': 'id', 'User-Agent': 'Mozilla/5.0'})
r_dw = dw.post(f'{BASE_DW}/anonymous/login', json={'device_id': dh},
               headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
d_dw = (dec(r_dw.text) or r_dw.json() or {}).get('data', {})
ak_dw = d_dw.get('auth_key', ''); ase_dw = d_dw.get('auth_secret', '')
print(f'DW Login: key={ak_dw[:8]}...')

def ah_dw():
    sig = hashlib.md5(f'{APP_SECRET}&{ase_dw}'.encode()).hexdigest()
    return {'authorization': f'oauth_signature={sig},oauth_token={ak_dw},ts={int(time.time()*1000)}'}

# ── FreeReels ────────────────────────────────────────────────────────────────
fr = requests.Session()
fr.headers.update({'app-name': 'com.freereels.app', 'device': 'android', 'app-version': '2.2.10',
                   'device-id': dh, 'device-hash': dh, 'country': 'ID', 'language': 'id',
                   'User-Agent': 'com.freereels.app/2.2.10'})
r_fr = fr.post(f'{BASE_FR}/anonymous/login', json={'device_id': dh},
               headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
d_fr = (r_fr.json() or {}).get('data', {})
ak_fr = d_fr.get('auth_key', ''); ase_fr = d_fr.get('auth_secret', '')
print(f'FR Login: key={ak_fr[:8]}...')

def ah_fr():
    sig = hashlib.md5(f'{APP_SECRET}&{ase_fr}'.encode()).hexdigest()
    return {'authorization': f'oauth_signature={sig},oauth_token={ak_fr},ts={int(time.time()*1000)}'}

print('\n=== Test drama/view with valid alphanumeric series_ids ===')

for sid in VALID_IDS:
    print(f'\n--- series_id={sid} ---')
    
    # DramaWave: drama/view POST (AES encrypted)
    for body in [
        {'series_id': sid},
        {'series_id': sid, 'audiotrack_language': 'id-ID'},
        {'series_id': sid, 'audiotrack_language': 'id'},
    ]:
        r3 = dw.post(f'{BASE_DW}/drama/view', data=enc(body),
                     headers={**ah_dw(), 'Content-Type': 'application/json'}, timeout=15)
        resp = dec(r3.text) or {}
        code = resp.get('code', '?'); msg = resp.get('message', '')[:40]
        print(f'  DW drama/view {body} -> code={code} msg={msg}')
        if code in [200, 0]:
            data = resp.get('data', {})
            print(f'  data keys: {list(data.keys())[:10]}')
            ep_list = data.get('episode_list', data.get('episodes', []))
            print(f'  episodes: {len(ep_list)}')
            if ep_list:
                ep = ep_list[0]
                print(f'  ep[0] ALL keys: {list(ep.keys())}')
                for k in ['id', 'title', 'external_audio_h264_m3u8', 'external_audio_h265_m3u8', 
                          'm3u8_url', 'video_url', 'hls_url', 'play_url', 'original_audio_language']:
                    if k in ep:
                        val = ep[k]
                        print(f'    {k}: {str(val)[:80]}')
            with open(f'drama_view_{sid}.json', 'w', encoding='utf-8') as f:
                json.dump(resp, f, ensure_ascii=False, indent=2)
            print(f'  Saved drama_view_{sid}.json')
            break

    # FreeReels API: drama/info GET
    r4 = fr.get(f'{BASE_FR}/drama/info', headers=ah_fr(),
                params={'series_id': sid}, timeout=10)
    resp4 = r4.json() if r4.ok else {}
    code4 = resp4.get('code', '?')
    print(f'  FR drama/info -> code={code4}')
    if code4 in [200, 0]:
        info = resp4.get('data', {}).get('info', resp4.get('data', {}))
        print(f'  info keys: {list(info.keys()) if isinstance(info, dict) else "N/A"}')

# Also test drama/info GET on DramaWave
print('\n=== DramaWave drama/info GET ===')
for sid in VALID_IDS:
    r5 = dw.get(f'{BASE_DW}/drama/info', headers=ah_dw(), params={'series_id': sid}, timeout=10)
    resp5 = dec(r5.text) or {}
    code5 = resp5.get('code', '?')
    data5 = resp5.get('data', {})
    info5 = data5.get('info', data5) if isinstance(data5, dict) else {}
    print(f'  series_id={sid}: code={code5}')
    if code5 in [200, 0] and info5:
        title = info5.get('title') or info5.get('name', '?')
        ep_list = info5.get('episode_list', [])
        print(f'  Title: {title}')
        print(f'  Episodes in info: {len(ep_list)}')
