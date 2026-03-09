"""
API Explorer: Discover DramaWave tabs and dubbing category
"""
import requests
import hashlib
import hmac as hmac_lib
import json
import time
import base64
import random
import string
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# --- Crypto ---
AES_KEY = b'2r36789f45q01ae5'

def aes_decrypt(text, key=AES_KEY):
    try:
        raw = base64.b64decode(text)
        iv, ct = raw[:16], raw[16:]
        k = key[:16].ljust(16, b'\x00')
        cipher = Cipher(algorithms.AES(k), modes.CBC(iv), backend=default_backend())
        dec = cipher.decryptor()
        padded = dec.update(ct) + dec.finalize()
        pad_len = padded[-1]
        return json.loads(padded[:-pad_len].decode('utf-8'))
    except Exception as e:
        return {'_error': str(e), '_raw': text[:100]}

def aes_encrypt(data, key=AES_KEY):
    import os as _os
    payload = json.dumps(data, separators=(',', ':')).encode()
    # PKCS7 pad to 16-byte blocks
    pad = 16 - (len(payload) % 16)
    payload += bytes([pad] * pad)
    iv = _os.urandom(16)
    k = key[:16].ljust(16, b'\x00')
    cipher = Cipher(algorithms.AES(k), modes.CBC(iv), backend=default_backend())
    enc = cipher.encryptor()
    ct = enc.update(payload) + enc.finalize()
    return base64.b64encode(iv + ct).decode()

# --- Auth ---
BASE_URL = 'https://api.mydramawave.com/h5-api'
device_hash = '45b1e5fc4217ac75219db8294ca16037'
auth_key    = 'ZVB4l2QYMHknsmbYoF1QVvytymDzsj1M'
auth_secret = 'N2AJeVsX6wue1i25WLh974JKsZVxHSIk'

def auth_header():
    ts  = str(int(time.time() * 1000))
    msg = f'oauth_token={auth_key}&ts={ts}'
    sig = hmac_lib.new(auth_secret.encode(), msg.encode(), hashlib.md5).hexdigest()
    return {'authorization': f'oauth_signature={sig},oauth_token={auth_key},ts={ts}'}

def base_headers():
    return {
        'app-name': 'com.dramawave.h5',
        'device': 'h5',
        'app-version': '1.2.20',
        'device-id': device_hash,
        'device-hash': device_hash,
        'country': 'ID',
        'language': 'id',
        'shortcode': 'id',
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 12)',
    }

sess = requests.Session()
sess.headers.update(base_headers())

def api_get(path, params=None):
    r = sess.get(BASE_URL + path, headers=auth_header(), params=params, timeout=15)
    print(f'GET {path} -> {r.status_code}')
    if r.status_code == 200:
        return aes_decrypt(r.text)
    return {'status': r.status_code, 'text': r.text[:200]}

def api_post(path, body=None):
    body = body or {}
    enc  = aes_encrypt(body)
    hdrs = {**auth_header(), 'Content-Type': 'text/plain'}
    r = sess.post(BASE_URL + path, data=enc, headers=hdrs, timeout=15)
    print(f'POST {path} body={json.dumps(body)} -> {r.status_code}')
    if r.status_code == 200:
        return aes_decrypt(r.text)
    return {'status': r.status_code, 'text': r.text[:200]}

print('=' * 60)
print('1. Fetching homepage tabs (language=id, country=ID)...')
resp = api_get('/homepage/v2/tab/list')
print(json.dumps(resp, indent=2, ensure_ascii=False)[:2000])

print()
print('=' * 60)
print('2. Also try without language filter...')
old_headers = dict(sess.headers)
sess.headers.update({'language': 'en', 'country': 'US', 'shortcode': 'en'})
resp2 = api_get('/homepage/v2/tab/list')
print(json.dumps(resp2, indent=2, ensure_ascii=False)[:2000])
sess.headers.update(old_headers)

print()
print('=' * 60)
print('3. Try anonymous login to get fresh token...')
resp3 = api_post('/anonymous/login', {})
print(json.dumps(resp3, indent=2, ensure_ascii=False)[:1000])
