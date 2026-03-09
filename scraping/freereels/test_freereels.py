"""
Test FreeReels API for dubbed drama content.
1. Test drama/info with alphanumeric IDs (same as DramaWave?)
2. Test all possible tab feed methods for tab_key=514 (Dubbed)
3. Capture web.free-reels.com via browser intercept
"""
import sys, json, time, base64, hashlib, os, re
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
AES_KEY    = b'2r36789f45q01ae5'
BASE       = 'https://apiv2.free-reels.com/frv2-api'

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

# Login
dh = hashlib.md5(b'freereels_scraper_v1_kingshortid').hexdigest()
sess = requests.Session()
sess.headers.update({
    'app-name': 'com.freereels.app', 'device': 'android', 'app-version': '2.2.10',
    'device-id': dh, 'device-hash': dh, 'country': 'ID', 'language': 'id',
    'User-Agent': 'com.freereels.app/2.2.10',
})
r = sess.post(f'{BASE}/anonymous/login', json={'device_id': dh},
              headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
d = (r.json() or {}).get('data', {})
ak = d.get('auth_key', ''); ase = d.get('auth_secret', '')
print(f'FR Login: key={ak[:8]}... uid={d.get("user_id")}')

def ah():
    sig = hashlib.md5(f'{APP_SECRET}&{ase}'.encode()).hexdigest()
    return {'authorization': f'oauth_signature={sig},oauth_token={ak},ts={int(time.time()*1000)}'}

print('\n=== Test 1: drama/info with alphanumeric IDs ===')
for sid in ['Cdg4Th1kpv', '8hX52C1Do1']:
    r2 = sess.get(f'{BASE}/drama/info', headers=ah(), params={'series_id': sid}, timeout=15)
    resp = r2.json() if r2.ok else {}
    code = resp.get('code', '?')
    print(f'  series_id={sid}: code={code} msg={resp.get("message","")[:40]}')
    if code in [200, 0]:
        data = resp.get('data', {})
        info = data.get('info', data)
        print(f'  → Title: {info.get("name", "?")}')
        print(f'  → Episodes: {info.get("episode_count", "?")}')
        ep_list = info.get('episode_list', [])
        if ep_list:
            ep0 = ep_list[0]
            for k in ['external_audio_h264_m3u8', 'audio', 'm3u8_url']:
                if k in ep0: print(f'    {k}: {str(ep0[k])[:60]}')
        with open(f'fr_drama_info_{sid}.json', 'w', encoding='utf-8') as f:
            json.dump(resp, f, ensure_ascii=False, indent=2)

print('\n=== Test 2: Tab 514 (Dubbed) Feed — All Methods ===')
for body in [
    {'tab_key': '514'},
    {'tab_key': '514', 'page': 1, 'page_size': 20},
    {'tab_key': '514', 'page': 0, 'page_size': 20},
    {'tab_key': 514, 'page': 1, 'page_size': 20},
    {'tab_key': '514', 'page_num': 1, 'page_size': 20},
    {'tab_key': '514', 'page': 1, 'page_size': 20, 'module_key': '1'},
    {'tab_key': '514', 'index': 1, 'size': 20},
    {'id': '514', 'page': 1, 'page_size': 20},
]:
    # AES encrypted POST
    r3 = sess.post(f'{BASE}/homepage/v2/tab/feed', data=enc(body),
                   headers={**ah(), 'Content-Type': 'application/json'}, timeout=10)
    resp3 = dec(r3.text) or r3.json() if r3.ok else {}
    code3 = resp3.get('code', '?')
    items3 = (resp3.get('data') or {}).get('list', []) if code3 in [200, 0] else []
    print(f'  AES {body} → {code3} [{len(items3)} items]')
    if items3:
        print(f'  → GOT {len(items3)} dramas from tab 514!')
        with open('fr_tab514_feed.json', 'w', encoding='utf-8') as f:
            json.dump(resp3, f, ensure_ascii=False, indent=2)
        break

print('\n=== Test 3: Explore other FR endpoints ===')
for path in ['/drama/list', '/drama/recommend', '/category/list', '/homepage/v2/page']:
    for body in [{'page': 1, 'page_size': 20}, {'lang': 'id'}]:
        try:
            r4 = sess.post(f'{BASE}{path}', data=enc(body),
                           headers={**ah(), 'Content-Type': 'application/json'}, timeout=10)
            resp = dec(r4.text) or {}
            code = resp.get('code', '?')
            items = []
            if isinstance(resp.get('data'), dict):
                items = resp['data'].get('list', resp['data'].get('dramas', []))
            elif isinstance(resp.get('data'), list):
                items = resp['data']
            print(f'  POST {path}: code={code} items={len(items)}')
            if items:
                ids = [str(i.get('id','')) for i in items[:3] if i.get('id')]
                print(f'    Sample IDs: {ids}')
                with open(f'fr_path_{path.replace("/","_")}.json', 'w') as f:
                    json.dump(resp, f, ensure_ascii=False, indent=2)
        except: pass

print('\n=== Test 4: Tab Index (might need before tab/feed) ===')
tab_idx_resp = sess.get(f'{BASE}/homepage/v2/tab/index',
                         params={'tab_key': '514'}, headers=ah(), timeout=10)
idx = tab_idx_resp.json() if tab_idx_resp.ok else {}
print(f'  tab/index tab_key=514: code={idx.get("code","?")} data={str(idx.get("data",""))[:100]}')

# Also try with different app headers (maybe web version)
print('\n=== Test 5: Try as web/H5 client ===')
sess_web = requests.Session()
sess_web.headers.update({
    'app-name': 'com.freereels.h5', 'device': 'h5', 'app-version': '1.0.0',
    'device-id': dh, 'device-hash': dh, 'country': 'ID', 'language': 'id',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 12)',
})
r_web = sess_web.post(f'{BASE}/anonymous/login', json={'device_id': dh},
                      headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
web_d = (dec(r_web.text) or r_web.json() or {}).get('data', {})
web_ak = web_d.get('auth_key', '')
if web_ak:
    print(f'  Web login OK: key={web_ak[:8]}...')
    web_ase = web_d.get('auth_secret', '')
    def ah_web():
        sig = hashlib.md5(f'{APP_SECRET}&{web_ase}'.encode()).hexdigest()
        return {'authorization': f'oauth_signature={sig},oauth_token={web_ak},ts={int(time.time()*1000)}'}
    r5 = sess_web.post(f'{BASE}/homepage/v2/tab/feed',
                       data=enc({'tab_key': '514', 'page': 1, 'page_size': 20}),
                       headers={**ah_web(), 'Content-Type': 'application/json'}, timeout=10)
    resp5 = dec(r5.text) or {}
    items5 = (resp5.get('data') or {}).get('list', [])
    print(f'  Web tab/514/feed: code={resp5.get("code","?")} items={len(items5)}')
