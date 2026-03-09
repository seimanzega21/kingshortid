"""
Scan free-reels.com to find FreeReels series ID format and
correct API parameters for tab 514 (Dubbed).
"""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

URLS = [
    'https://free-reels.com/',
    'https://www.free-reels.com/',
    'https://m.free-reels.com/',
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 12)',
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
}

print('=== Scanning free-reels.com pages ===')
for url in URLS:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        print(f'\n{url} → {r.status_code} (final: {r.url})')
        html = r.text[:5000]
        
        # Look for series URLs
        drama_ids = re.findall(r'/(?:series|drama|watch|episode)/([A-Za-z0-9_-]{4,20})', html)
        print(f'  Drama IDs found: {list(set(drama_ids))[:10]}')
        
        # Look for API URLs
        apis = re.findall(r'https?://[a-z0-9.-]*free-reels[a-z0-9.-]*/[^\s"\'<>]{3,80}', html)
        print(f'  API URLs found: {list(set(apis))[:5]}')
        
        # Look for JS bundle
        js_urls = re.findall(r'(?:src|href)=["\']([^\s"\']+\.js)["\']', html)
        print(f'  JS bundles: {js_urls[:3]}')
        
        # Save HTML snippet
        with open(f'fr_html_{url.replace("://","_").replace("/","_")[:30]}.txt', 'w', encoding='utf-8', errors='replace') as f:
            f.write(r.text[:10000])
    except Exception as e:
        print(f'  ERROR: {e}')

# Try FreeReels API direct endpoints we havent tried
BASE = 'https://apiv2.free-reels.com/frv2-api'
import hashlib, time, base64, os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
AES_KEY = b'2r36789f45q01ae5'

def enc(data):
    payload = json.dumps(data, separators=(',', ':')).encode()
    pad = 16 - (len(payload) % 16); payload += bytes([pad] * pad)
    iv = os.urandom(16)
    c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
    e = c.encryptor(); return base64.b64encode(iv + e.update(payload) + e.finalize()).decode()

def dec(t):
    try:
        r = base64.b64decode(t); iv, ct = r[:16], r[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct) + c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(t)
        except: return None

dh = hashlib.md5(b'freereels_test_web').hexdigest()
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
print(f'\nFR API Login: key={ak[:8]}...')

def ah():
    sig = hashlib.md5(f'{APP_SECRET}&{ase}'.encode()).hexdigest()
    return {'authorization': f'oauth_signature={sig},oauth_token={ak},ts={int(time.time()*1000)}'}

print('\n=== Scan ALL possible drama collection endpoints ===')
endpoints = [
    '/drama/list',
    '/drama/hot',  
    '/drama/new',
    '/drama/category',
    '/drama/category/list',
    '/drama/search',
    '/homepage/v2/tab/content',
    '/homepage/v2/home',
    '/homepage/v2/page/list',
    '/category/drama/list',
    '/drama/dubbing/list',
    '/content/list',
]

for ep in endpoints:
    for method in ['GET', 'POST']:
        try:
            if method == 'GET':
                res = sess.get(f'{BASE}{ep}', headers=ah(), params={'page': 1, 'page_size': 20}, timeout=8)
            else:
                res = sess.post(f'{BASE}{ep}', data=enc({'page': 1, 'page_size': 20, 'tab_key': '514'}),
                               headers={**ah(), 'Content-Type': 'application/json'}, timeout=8)
            
            resp = dec(res.text) or {}
            code = resp.get('code', '?')
            msg = resp.get('message', '')[:30]
            data = resp.get('data', {})
            
            items = []
            if isinstance(data, list): items = data
            elif isinstance(data, dict):
                for k in ['list', 'dramas', 'data', 'items', 'feed']:
                    if isinstance(data.get(k), list):
                        items = data[k]; break
            
            status = f'code={code} items={len(items)} msg={msg}'
            print(f'  {method} {ep}: {status}')
            
            if len(items) > 0:
                ids = [str(item.get('id', '')) for item in items[:3] if item.get('id')]
                print(f'    → IDs: {ids}')
                with open(f'fr_ep_{ep.replace("/","_")}.json', 'w') as f:
                    json.dump(resp, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'  {method} {ep}: error {e.__class__.__name__}')
