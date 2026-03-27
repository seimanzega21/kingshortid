"""Debug FreeReels tab 514 feed - find correct series ID field"""
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

r = sess.post(f'{FR_BASE}/anonymous/login', json={'device_id': dh},
              headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
d = r.json().get('data', {})
ak  = d.get('auth_key', '')
ase = d.get('auth_secret', '')

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

# Test 1: Get page 1 of tab 514 and show ALL fields of first item
print("=== Tab 514 page 1 - checking all fields ===")
r = sess.post(f'{FR_BASE}/homepage/v2/tab/feed',
              json={'tab_key':'514','module_key':'514','page':1,'page_size':5},
              headers={**ah(),'Content-Type':'application/json','Skip-Encrypt':'1'}, timeout=15)
resp = r.json() if r.ok else {}
data = resp.get('data', {})
items = data.get('items') or data.get('list', [])
print(f"Got {len(items)} items")
if items:
    item = items[0]
    print("All fields in item:")
    for k, v in item.items():
        print(f"  {k}: {repr(v)[:100]}")

print()

# Test 2: Try drama/info with dubbed_series_ids IDs (known working)
print("=== Testing working IDs from dubbed_series_ids.json ===")
dubbed = json.loads(pathlib.Path('dubbed_series_ids.json').read_text(encoding='utf-8'))
for sid in list(dubbed.keys())[:2]:
    r = sess.get(f'{FR_BASE}/drama/info', headers=ah(),
                 params={'series_id': sid}, timeout=20)
    print(f"  {sid}: status={r.status_code}, len={len(r.text)}")
    decoded = dec(r.text)
    if decoded:
        code = decoded.get('code')
        info = decoded.get('data', {})
        if isinstance(info, dict):
            inner = info.get('info', info)
            name = inner.get('name', '?') if isinstance(inner, dict) else '?'
            print(f"    code={code} name={name}")
    time.sleep(0.5)

print()

# Test 3: Check if tab 514 items have a different ID linked to drama/info
print("=== Checking if tab items have drama_id or series_id alternative ===")
if items:
    for item in items[:3]:
        # Try all potential ID fields
        for id_field in ['key', 'id', 'series_id', 'drama_id', 'content_id']:
            val = item.get(id_field)
            if val:
                r = sess.get(f'{FR_BASE}/drama/info', headers=ah(),
                             params={'series_id': val}, timeout=15)
                print(f"  field={id_field} val={val} -> status={r.status_code} len={len(r.text)}")
                time.sleep(0.3)
