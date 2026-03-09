"""
DEFINITIVE test: Get module_key from tab/list for FreeReels tab 514,
then use it for tab/feed. Also try all device header variations.
This is the correct 3-step flow based on JS source analysis.
"""
import sys, json, time, base64, hashlib, os, re
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
AES_KEY    = b'2r36789f45q01ae5'
FR_BASE    = 'https://apiv2.free-reels.com/frv2-api'
DW_BASE    = 'https://api.mydramawave.com/h5-api'

def enc(data):
    payload = json.dumps(data, separators=(',',':')).encode()
    pad = 16 - (len(payload) % 16); payload += bytes([pad]*pad)
    iv = os.urandom(16)
    c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
    e = c.encryptor()
    return base64.b64encode(iv + e.update(payload) + e.finalize()).decode()

def dec(t):
    try:
        r = base64.b64decode(t); iv, ct = r[:16], r[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct) + c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(t)
        except: return None

def ah(ak, ase):
    sig = hashlib.md5(f'{APP_SECRET}&{ase}'.encode()).hexdigest()
    return {'authorization': f'oauth_signature={sig},oauth_token={ak},ts={int(time.time()*1000)}'}

# ─── Try different device profiles ─────────────────────────────────────────
DEVICE_PROFILES = [
    # Android app with different versions
    {'app-name': 'com.freereels.app', 'device': 'android', 'app-version': '2.2.10',
     'User-Agent': 'okhttp/4.12.0', 'os': 'android', 'os-version': '12'},
    {'app-name': 'com.freereels.app', 'device': 'android', 'app-version': '2.1.5',
     'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/SP1A)',
     'os': 'android', 'os-version': '12'},
    # iOS
    {'app-name': 'com.freereels.ios', 'device': 'ios', 'app-version': '2.2.8',
     'User-Agent': 'FreeReels/2.2.8 (iPhone; iOS 16.0)',
     'os': 'ios', 'os-version': '16.0'},
    # H5/Web
    {'app-name': 'com.freereels.h5', 'device': 'h5', 'app-version': '1.0.0',
     'User-Agent': 'Mozilla/5.0 (Linux; Android 12) FreeReelsWebApp/1.0'},
]

best_result = None

for profile in DEVICE_PROFILES:
    dh = hashlib.md5(f'freereels_{profile["device"]}_v3'.encode()).hexdigest()
    sess = requests.Session()
    base_headers = {**profile, 'device-id': dh, 'device-hash': dh,
                    'country': 'ID', 'language': 'id', 'shortcode': 'id',
                    'Accept': 'application/json', 'Accept-Language': 'id-ID,id;q=0.9'}
    sess.headers.update(base_headers)

    # Login
    r = sess.post(f'{FR_BASE}/anonymous/login', json={'device_id': dh},
                  headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
    login_data = r.json() if r.ok else {}
    login_d = (dec(r.text) or login_data).get('data', {})
    ak = login_d.get('auth_key', ''); ase = login_d.get('auth_secret', '')
    if not ak:
        print(f'[{profile["device"]} {profile["app-version"]}] Login FAILED')
        continue
    print(f'\n[{profile["device"]} {profile["app-version"]}] Login OK: key={ak[:8]}...')

    # Step 1: Get tab list and find module_key for tab 514
    tab_r = sess.get(f'{FR_BASE}/homepage/v2/tab/list', headers=ah(ak, ase), timeout=15)
    tab_resp = dec(tab_r.text) or tab_r.json() if tab_r.ok else {}
    tabs = (tab_resp.get('data') or {}).get('list', [])
    print(f'  Tabs: {len(tabs)} found')

    module_key_514 = None
    for tab in tabs:
        tkey = str(tab.get('tab_key', ''))
        tname = tab.get('business_name') or tab.get('name', '')
        mkey = tab.get('module_key') or tab.get('key') or tab.get('id')
        print(f'    tab_key={tkey} name={tname} module_key={mkey}')
        if tkey == '514':
            module_key_514 = mkey

    # Step 2: GET tab/index to get module_key (alternate way)
    for tk in ['514', 514]:
        idx_r = sess.get(f'{FR_BASE}/homepage/v2/tab/index',
                         params={'tab_key': tk}, headers=ah(ak, ase), timeout=10)
        idx_resp = dec(idx_r.text) or {}
        idx_code = idx_resp.get('code', '?')
        idx_data = idx_resp.get('data', {})
        if idx_code in [200, 0] and idx_data:
            mkey = idx_data.get('module_key') or idx_data.get('key')
            print(f'  tab/index tab_key={tk}: code={idx_code} module_key={mkey}')
            if mkey and not module_key_514:
                module_key_514 = mkey

    print(f'  module_key for tab 514: {module_key_514}')

    # Step 3: Try tab/feed with module_key and every possible body combo
    bodies_to_try = []
    if module_key_514:
        bodies_to_try += [
            {'module_key': module_key_514, 'page': 1, 'page_size': 20},
            {'module_key': str(module_key_514), 'page': 1, 'page_size': 20},
            {'module_key': module_key_514, 'tab_key': '514', 'page': 1, 'page_size': 20},
        ]
    bodies_to_try += [
        {'tab_key': '514', 'page': 1, 'page_size': 20},
        {'tab_key': 514, 'page': 1, 'page_size': 20},
        {'tab_key': '514', 'page': 1, 'page_size': 20, 'lang': 'id'},
        {'tab_key': '514', 'module_key': '514', 'page': 1, 'page_size': 20},
    ]

    for body in bodies_to_try:
        for post_fn_name, post_fn in [
            ('AES', lambda b: sess.post(f'{FR_BASE}/homepage/v2/tab/feed',
                data=enc(b), headers={**ah(ak, ase), 'Content-Type': 'application/json'}, timeout=10)),
            ('PLAIN', lambda b: sess.post(f'{FR_BASE}/homepage/v2/tab/feed',
                json=b, headers={**ah(ak, ase), 'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=10)),
        ]:
            try:
                res = post_fn(body)
                resp = dec(res.text) or res.json() if res.ok else {}
                code = resp.get('code', '?')
                items = []
                if isinstance(resp.get('data'), dict):
                    for k in ['list', 'dramas', 'feed', 'items']:
                        if isinstance(resp['data'].get(k), list):
                            items = resp['data'][k]; break
                if code in [200, 0] and items:
                    print(f'  ✓✓✓ {post_fn_name} {body}: code={code} ITEMS={len(items)}!')
                    with open('fr_tab514_SUCCESS.json', 'w', encoding='utf-8') as f:
                        json.dump(resp, f, ensure_ascii=False, indent=2)
                    best_result = items
                    break
                elif code not in ['?'] and code not in [400, 401]:
                    print(f'  ! {post_fn_name}: code={code} msg={resp.get("message","")[:30]}')
            except: pass
        if best_result: break
    if best_result: break
    time.sleep(0.5)

if best_result:
    print(f'\n\n✓ SUCCESS! Got {len(best_result)} items from tab 514')
    ids = [str(i.get('id', '')) for i in best_result[:10] if i.get('id')]
    print(f'Sample IDs: {ids}')
else:
    print('\n\nAll approaches FAILED → FreeReels definitively blocks anonymous tab/feed')
    print('\nFinal verdict: FreeReels API requires authenticated (real) user account')
    print('Cannot proceed without real user credentials or device intercept.')
