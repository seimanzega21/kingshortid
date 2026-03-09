"""
Query FreeReels API (apiv2.free-reels.com) - find tabs + dubbed category
"""
import requests
import json
import base64
import time
import hashlib
import hmac as hmac_lib
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

AES_KEY = b'2r36789f45q01ae5'

def aes_decrypt(text):
    try:
        raw = base64.b64decode(text)
        iv, ct = raw[:16], raw[16:]
        cipher = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        dec = cipher.decryptor()
        padded = dec.update(ct) + dec.finalize()
        pad_len = padded[-1]
        return json.loads(padded[:-pad_len].decode())
    except:
        return None

def aes_encrypt(data):
    payload = json.dumps(data, separators=(',', ':')).encode()
    pad = 16 - (len(payload) % 16)
    payload += bytes([pad] * pad)
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
    enc = cipher.encryptor()
    return base64.b64encode(iv + enc.update(payload) + enc.finalize()).decode()

BASE = 'https://apiv2.free-reels.com/frv2-api'
DW_BASE = 'https://api.mydramawave.com/h5-api'

device_hash = '45b1e5fc4217ac75219db8294ca16037'

# FreeReels doesn't need OAuth initially — test without auth first
sess = requests.Session()
sess.headers.update({
    'app-name': 'com.freereels.app',
    'device': 'android',
    'app-version': '2.2.10',
    'device-id': device_hash,
    'device-hash': device_hash,
    'country': 'ID',
    'language': 'id',
    'User-Agent': 'com.freereels.app/2.2.10 (Android 12)',
    'Accept': '*/*',
})

def call(method, url, body=None, try_decrypt=True):
    try:
        if method == 'GET':
            r = sess.get(url, timeout=12)
        else:
            # Try encrypted first, then JSON
            try:
                enc = aes_encrypt(body or {})
                r = sess.post(url, data=enc, headers={'Content-Type': 'text/plain'}, timeout=12)
            except:
                r = sess.post(url, json=body or {}, timeout=12)
        
        print(f'{r.status_code} {method} {url.replace(BASE, "").replace(DW_BASE, "")}')
        
        if r.status_code == 200 and try_decrypt:
            dec = aes_decrypt(r.text)
            if dec:
                return dec
            # Try raw JSON
            try:
                return r.json()
            except:
                return {'raw': r.text[:200]}
        return {'http': r.status_code, 'text': r.text[:150]}
    except Exception as e:
        print(f'  ERR: {e}')
        return {}

# 1. FreeReels anonymous login
print('=== 1. FreeReels Anonymous Login ===')
login_bodies = [
    {'deviceId': device_hash},
    {'device_id': device_hash, 'platform': 'android'},
    {'deviceHash': device_hash, 'appName': 'com.freereels.app'},
    {'client_id': 'com.freereels.app', 'grant_type': 'client_credentials'},
]
for b in login_bodies:
    resp = call('POST', f'{BASE}/anonymous/login', b)
    code = resp.get('code', resp.get('http', '?'))
    msg  = resp.get('message', '')
    data = resp.get('data', {})
    print(f'  body={list(b.keys())} code={code} msg={msg[:40]}')
    if code in [200, 0]:
        print(f'  *** SUCCESS: {json.dumps(data)[:200]} ***')
        break
    time.sleep(0.3)

# 2. FreeReels tabs without auth (maybe public)
print()
print('=== 2. FreeReels Tab List (no auth) ===')
resp = call('GET', f'{BASE}/homepage/v2/tab/list')
print(json.dumps(resp, indent=2, ensure_ascii=False)[:3000])

# 3. Also try DramaWave tablist with fresh anon token
print()
print('=== 3. DramaWave Tab List (with old token) ===')
auth_key    = 'ZVB4l2QYMHknsmbYoF1QVvytymDzsj1M'
auth_secret = 'N2AJeVsX6wue1i25WLh974JKsZVxHSIk'

ts  = str(int(time.time() * 1000))
sig = hmac_lib.new(auth_secret.encode(),
                   f'oauth_token={auth_key}&ts={ts}'.encode(),
                   hashlib.md5).hexdigest()
auth_val = f'oauth_signature={sig},oauth_token={auth_key},ts={ts}'

dw_sess = requests.Session()
dw_sess.headers.update({
    'app-name': 'com.dramawave.h5',
    'device': 'h5',
    'app-version': '1.2.20',
    'device-id': device_hash,
    'device-hash': device_hash,
    'country': 'ID',
    'language': 'id',
    'shortcode': 'id',
    'authorization': auth_val,
    'User-Agent': 'Mozilla/5.0',
    'Accept': '*/*',
})

r = dw_sess.get(f'{DW_BASE}/homepage/v2/tab/list', timeout=12)
print(f'{r.status_code} GET /homepage/v2/tab/list')
if r.status_code == 200:
    dec = aes_decrypt(r.text)
    if dec:
        print(json.dumps(dec, indent=2, ensure_ascii=False)[:3000])
    else:
        print(r.text[:200])
