import requests
import hashlib
import json
import base64
import time

BASE = 'https://api.mydramawave.com/h5-api'

# Live captured auth (may expire soon)
auth_token = 'oauth_signature=ed989f9678ed2bd017ad936309a1ea41,oauth_token=ZVB4l2QYMHknsmbYoF1QVvytymDzsj1M,ts=1773026884505'
device_hash = '45b1e5fc4217ac75219db8294ca16037'
auth_secret = 'N2AJeVsX6wue1i25WLh974JKsZVxHSIk'
auth_key = 'ZVB4l2QYMHknsmbYoF1QVvytymDzsj1M'

headers = {
    'authorization': auth_token,
    'app-name': 'com.dramawave.h5',
    'device': 'h5',
    'app-version': '1.2.20',
    'device-id': device_hash,
    'device-hash': device_hash,
    'shortcode': 'en',
    'country': 'US',
    'Accept': '*/*',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36',
}

session = requests.Session()
session.headers.update(headers)

# Test endpoints
endpoints = [
    ('GET', '/homepage/v2/tab/list', None),
    ('POST', '/anonymous/login', {}),
    ('POST', '/homepage/v2/tab/feed', {'tabId': 'for_you', 'page': 1, 'size': 10}),
    ('POST', '/drama/view', {'dramaId': 1}),
]

for method, path, body in endpoints:
    url = BASE + path
    try:
        if method == 'GET':
            r = session.get(url, timeout=10)
        else:
            r = session.post(url, json=body, timeout=10)

        print(f'=== {method} {path} ===')
        print(f'Status: {r.status_code}')
        print(f'Content-Type: {r.headers.get("Content-Type", "")}')

        # Check if JSON or encrypted
        raw = r.content[:500]
        try:
            data = r.json()
            print(f'JSON Response: {json.dumps(data, indent=2)[:400]}')
        except:
            # Try base64 decode
            try:
                decoded = base64.b64decode(raw)
                print(f'Base64 decoded: {decoded[:200]}')
            except:
                print(f'Raw text: {r.text[:200]}')
        print()

    except Exception as e:
        print(f'ERROR {path}: {e}')
        print()

print('--- Done ---')

# Also try to regenerate auth using secret
print('\n=== Testing new auth with captured secret ===')
ts = int(time.time() * 1000)
# Pattern: likely HMAC-SHA256 of some message using auth_secret as key
import hmac
import hashlib

# Try common signing patterns
message_candidates = [
    auth_key,
    f'{auth_key}{ts}',
    str(ts),
    f'oauth_token={auth_key}&ts={ts}',
]

print(f'auth_key: {auth_key}')
print(f'auth_secret: {auth_secret}')
print(f'ts: {ts}')
for msg in message_candidates:
    sig = hmac.new(auth_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    print(f'HMAC-SHA256({repr(msg)}): {sig}')
    sig_md5 = hmac.new(auth_secret.encode(), msg.encode(), hashlib.md5).hexdigest()
    print(f'HMAC-MD5({repr(msg)}): {sig_md5}')
