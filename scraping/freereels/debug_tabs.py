"""Read drama/info response for Cdg4Th1kpv and inspect episode_list audio fields."""
import sys, json, time, base64, hashlib, os
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AES_KEY = b'2r36789f45q01ae5'; APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
BASE = 'https://api.mydramawave.com/h5-api'

def dec(t):
    try:
        r = base64.b64decode(t); iv, ct = r[:16], r[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct) + c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(t)
        except: return None

dh = hashlib.md5(b'freereels_scraper_v1_kingshortid').hexdigest()
sess = requests.Session()
sess.headers.update({'app-name': 'com.dramawave.h5', 'device': 'h5', 'app-version': '1.2.20',
                     'device-id': dh, 'device-hash': dh, 'country': 'ID', 'language': 'id',
                     'shortcode': 'id', 'User-Agent': 'Mozilla/5.0'})
r = sess.post(f'{BASE}/anonymous/login', json={'device_id': dh},
              headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
d = (dec(r.text) or r.json() or {}).get('data', {})
ak = d.get('auth_key', ''); ase = d.get('auth_secret', '')
print(f'Login: key={ak[:8]}...')

def ah():
    sig = hashlib.md5(f'{APP_SECRET}&{ase}'.encode()).hexdigest()
    return {'authorization': f'oauth_signature={sig},oauth_token={ak},ts={int(time.time()*1000)}'}

# Fetch drama info with episode list
sid = 'Cdg4Th1kpv'
r2 = sess.get(f'{BASE}/drama/info', headers=ah(), params={'series_id': sid}, timeout=15)
resp = dec(r2.text) or {}
data = resp.get('data', {})
info = data.get('info', data) if isinstance(data, dict) else {}

print(f'\nDrama: {info.get("title", "?")}')
print(f'Data keys: {list(data.keys())}')
print(f'Info keys: {list(info.keys()) if isinstance(info, dict) else "N/A"}')

# Save full response
with open('drama_info_full.json', 'w', encoding='utf-8') as f:
    json.dump(resp, f, ensure_ascii=False, indent=2)
print(f'Saved drama_info_full.json')

# Inspect episode list
ep_list = info.get('episode_list') or data.get('episode_list', [])
print(f'\nEpisodes in episode_list: {len(ep_list)}')

if ep_list:
    ep = ep_list[0]
    print(f'\nEpisode[0] keys ({len(ep.keys())} total):')
    # Print ALL keys
    for k, v in ep.items():
        val_str = str(v)[:80] if v else ''
        print(f'  {k}: {val_str}')

# Also check top-level data for audio/episode-related fields
print(f'\nTop-level data (non-list fields):')
for k, v in data.items():
    if not isinstance(v, list):
        print(f'  {k}: {str(v)[:80]}')
