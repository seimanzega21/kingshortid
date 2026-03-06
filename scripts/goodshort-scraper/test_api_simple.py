"""
Simple test: Can we use API without signing?
"""

import requests
import json
import sys

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Extract token
har_file = "HTTPToolkit_2026-02-03_00-53.har"

with open(har_file, 'r', encoding='utf-8') as f:
    har = json.load(f)

# Find auth token
auth_token = None
for entry in har['log']['entries']:
    for header in entry['request']['headers']:
        if header['name'].lower() == 'authorization':
            auth_token = header['value']
            break
    if auth_token:
        break

print(f"Token: {auth_token[:40]}...")

# Test simple GET
url = "https://api-akm.goodreels.com/hwycclientreels/book/shelf/allList"

headers = {
    'authorization': auth_token,
    'user-agent': 'okhttp/4.10.0'
}

print(f"\nTesting: {url}")
print("Without 'sign' header...")

try:
    resp = requests.get(url, headers=headers, params={'timestamp': '1770054370944'}, timeout=15)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        print("SUCCESS - Signing NOT required!")
        data = resp.json()
        print(f"Response has {len(str(data))} chars")
    else:
        print(f"FAILED - {resp.status_code}")
        print(resp.text[:200])

except Exception as e:
    print(f"Error: {e}")
