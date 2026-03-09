"""
Test: apakah FreeReels anonymous login sudah unlock semua episode?
Ambil 5 drama dari freereels_series_ids.json, cek berapa episode punya HLS URL.
"""
import sys, json, time, base64, hashlib, os
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
AES_KEY    = b'2r36789f45q01ae5'
FR_BASE    = 'https://apiv2.free-reels.com/frv2-api'

def dec(t):
    try:
        r = base64.b64decode(t); iv, ct = r[:16], r[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct) + c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(t)
        except: return None

dh = hashlib.md5(b'freereels_test_episodes').hexdigest()
sess = requests.Session()
sess.headers.update({
    'app-name':'com.freereels.app', 'device':'android',
    'app-version':'2.2.10', 'device-id':dh, 'device-hash':dh,
    'country':'ID', 'language':'id', 'User-Agent':'okhttp/4.12.0',
})
r = sess.post(f'{FR_BASE}/anonymous/login', json={'device_id':dh},
              headers={'Content-Type':'application/json','Skip-Encrypt':'1'}, timeout=15)
d = (r.json() if r.ok else {}).get('data', {})
ak = d.get('auth_key',''); ase = d.get('auth_secret','')
print(f'[AUTH] key={ak[:8]}...')

def ah():
    sig = hashlib.md5(f'{APP_SECRET}&{ase}'.encode()).hexdigest()
    return {'authorization': f'oauth_signature={sig},oauth_token={ak},ts={int(time.time()*1000)}'}

# Load series IDs
with open('freereels_series_ids.json', encoding='utf-8') as f:
    series = json.load(f)

# Test first 5 dramas
print(f'\nTesting {min(5, len(series))} dramas from FreeReels tab 514...\n')
series_list = list(series.items())[:5]

for sid, meta in series_list:
    r2 = sess.get(f'{FR_BASE}/drama/info', headers=ah(), params={'series_id': sid}, timeout=20)
    resp = dec(r2.text) or r2.json() if r2.ok else {}
    code = resp.get('code', '?')
    
    if code not in [200, 0]:
        print(f'  {sid}: FAILED code={code}')
        continue
    
    data = resp.get('data', {})
    info = data.get('info', data) if isinstance(data, dict) else {}
    ep_list = info.get('episode_list', [])
    
    total = len(ep_list)
    with_hls = [ep for ep in ep_list if ep.get('external_audio_h264_m3u8','') or ep.get('m3u8_url','')]
    with_id_audio = [ep for ep in ep_list if 'id-ID' in ep.get('audio', [])]
    locked = [ep for ep in ep_list if not ep.get('external_audio_h264_m3u8','') and not ep.get('m3u8_url','')]
    
    print(f'Drama: {info.get("name","?")[:50]}')
    print(f'  Series ID: {sid}')
    print(f'  Total eps: {total}')
    print(f'  HLS URL ada: {len(with_hls)} eps')
    print(f'  id-ID audio: {len(with_id_audio)} eps')
    print(f'  Locked (no URL): {len(locked)} eps')
    
    if with_hls:
        print(f'  Sample HLS: {with_hls[0].get("external_audio_h264_m3u8","")[:80]}')
    
    # Check video_type field
    free_eps = [ep for ep in ep_list if ep.get('video_type') == 'free']
    paid_eps = [ep for ep in ep_list if ep.get('video_type') == 'vip' or ep.get('is_lock')]
    print(f'  Free type: {len(free_eps)}  Paid/VIP type: {len(paid_eps)}')
    print()
    time.sleep(0.5)

print('='*50)
print('KESIMPULAN:')
print('Kalau "Locked (no URL)" = 0 → anonymous sudah unlock semua episode di FreeReels!')
print('Kalau banyak yang locked → perlu login dengan akun Google')
