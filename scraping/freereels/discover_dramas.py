"""
Stage 1: Discover 200+ Dubbed Drama IDs from DramaWave
========================================================
Scans the DramaWave website to collect alphanumeric series_id values
for dramas that have Indonesian dubbed audio (tag: "Dubbing").

Run: python discover_dramas.py
Output: dubbed_series_ids.json
"""
import requests, re, json, time, base64, hashlib, os, sys
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
AES_KEY    = b'2r36789f45q01ae5'
BASE       = 'https://api.mydramawave.com/h5-api'
OUTPUT     = 'dubbed_series_ids.json'
TARGET     = 200

def dec(t):
    try:
        r = base64.b64decode(t); iv, ct = r[:16], r[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct) + c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(t)
        except: return None

# ── Login ────────────────────────────────────────────────────────────────────
dh = hashlib.md5(b'freereels_discover_v1').hexdigest()
sess = requests.Session()
sess.headers.update({
    'app-name': 'com.dramawave.h5', 'device': 'h5', 'app-version': '1.2.20',
    'device-id': dh, 'device-hash': dh, 'country': 'ID', 'language': 'id',
    'shortcode': 'id', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12)',
})
r = sess.post(f'{BASE}/anonymous/login', json={'device_id': dh},
              headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
d = (dec(r.text) or r.json() or {}).get('data', {})
ak = d.get('auth_key', ''); ase = d.get('auth_secret', '')
print(f'Login: key={ak[:8]}...')

def ah():
    sig = hashlib.md5(f'{APP_SECRET}&{ase}'.encode()).hexdigest()
    return {'authorization': f'oauth_signature={sig},oauth_token={ak},ts={int(time.time()*1000)}'}

# ── Seed IDs ─────────────────────────────────────────────────────────────────
# Start with confirmed IDs + scan homepage for more
seed_ids = {
    'Cdg4Th1kpv': 'Bertahan Hidup di Sekolah Elite (Sulih Suara)',
    '8hX52C1Do1': 'Terbangun sebagai Suami Terburuknya (Sulih Suara)',
}

# Try to get more from homepage/popular tab (scan different pages)
discovered_raw = set(seed_ids.keys())

# ── Web Scraping from DramaWave pages ─────────────────────────────────────────
print('\nScanning DramaWave web pages for series IDs...')
pages_to_scan = [
    'https://m.mydramawave.com/',
    'https://m.mydramawave.com/free-app/',
    'https://www.mydramawave.com/',
]

# Additional scan via search API for dubbed/sulih suara dramas
def search_api(keyword, page=1):
    """Search drama API."""
    for body in [{'keyword': keyword, 'page': page, 'page_size': 20}]:
        try:
            r2 = sess.post(f'{BASE}/search/drama', data=enc(body),
                          headers={**ah(), 'Content-Type': 'application/json'}, timeout=15)
            resp = dec(r2.text) or {}
            if resp.get('code') in [200, 0]:
                return (resp.get('data') or {}).get('list', [])
        except: pass
    return []

def enc(data):
    payload = json.dumps(data, separators=(',', ':')).encode()
    pad = 16 - (len(payload) % 16); payload += bytes([pad] * pad)
    iv = os.urandom(16)
    c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
    e = c.encryptor(); return base64.b64encode(iv + e.update(payload) + e.finalize()).decode()

for url in pages_to_scan:
    try:
        r3 = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12)',
            'Accept-Language': 'id-ID,id;q=0.9',
        })
        ids = re.findall(r'/series/([A-Za-z0-9]{8,12})', r3.text)
        discovered_raw.update(ids)
        print(f'  {url[:50]}: +{len(ids)} IDs')
    except Exception as e:
        print(f'  {url[:50]}: error {e}')

# ── Validate and filter for DUBBED ───────────────────────────────────────────
print(f'\nScreening {len(discovered_raw)} candidate IDs for Indonesian dubbed audio...')
dubbed_dramas = {}
failed = []

# Load existing results if resuming
if os.path.exists(OUTPUT):
    with open(OUTPUT, 'r', encoding='utf-8') as f:
        dubbed_dramas = json.load(f)
    print(f'Loaded {len(dubbed_dramas)} existing entries from {OUTPUT}')
    discovered_raw -= set(dubbed_dramas.keys())

for i, sid in enumerate(sorted(discovered_raw)):
    if sid in dubbed_dramas:
        continue
    if len(dubbed_dramas) >= TARGET:
        print(f'Target of {TARGET} reached!')
        break
        
    try:
        r4 = sess.get(f'{BASE}/drama/info', headers=ah(),
                      params={'series_id': sid}, timeout=15)
        resp = dec(r4.text) or {}
        if resp.get('code') not in [200, 0]:
            continue
        
        info = (resp.get('data') or {}).get('info', {})
        if not info: continue
        
        name   = info.get('name', '')
        tags   = info.get('tag', [])
        s_tags = info.get('series_tag', [])
        eps    = info.get('episode_list', [])
        ep_cnt = info.get('episode_count', 0)
        
        # Check if has Indonesian dubbed audio
        has_indo = False
        is_dubbing = 'Dubbing' in tags
        if eps:
            ep0_audio = eps[0].get('audio', [])
            has_indo = 'id-ID' in ep0_audio
            has_ext  = bool(eps[0].get('external_audio_h264_m3u8', ''))
            has_indo = has_indo or has_ext
        elif is_dubbing:
            has_indo = True  # Trust tag if no episode data
        
        if has_indo or is_dubbing:
            dubbed_dramas[sid] = {
                'series_id': sid,
                'title':     name,
                'tags':      tags,
                'genres':    s_tags,
                'episodes':  ep_cnt,
                'cover':     info.get('cover', ''),
                'desc':      info.get('desc', ''),
                'status':    'complete' if info.get('finish_status') == 2 else 'ongoing',
                'content_tags': info.get('content_tags', []),
            }
            marker = '✓ ' + ('DUBBING' if is_dubbing else 'ID-AUDIO')
            print(f'  [{i+1:03d}] {marker}: {name[:40]} ({ep_cnt} eps)')
            
            # Save progress
            with open(OUTPUT, 'w', encoding='utf-8') as f:
                json.dump(dubbed_dramas, f, ensure_ascii=False, indent=2)
        
        time.sleep(0.4)
        
    except Exception as e:
        print(f'  [{i+1:03d}] ERROR {sid}: {e}')
        failed.append(sid)

print(f'\n{"="*50}')
print(f'Dubbed dramas found: {len(dubbed_dramas)}')
print(f'Saved → {OUTPUT}')
with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(dubbed_dramas, f, ensure_ascii=False, indent=2)
