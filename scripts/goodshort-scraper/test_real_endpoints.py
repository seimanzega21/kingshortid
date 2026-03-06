"""
Test REAL endpoints from HAR without signing
"""

import requests
import json
import time

# Get token
har = json.load(open('HTTPToolkit_2026-02-03_00-53.har', 'r', encoding='utf-8'))
auth_token = None
for entry in har['log']['entries']:
    for h in entry['request']['headers']:
        if h['name'].lower() == 'authorization':
            auth_token = h['value']
            break
    if auth_token:
        break

print(f"Auth: {auth_token[:50]}...")

# Test 1: Chapter list (from HAR)
print("\n" + "="*60)
print("TEST: /hwycclientreels/chapter/list")
print("="*60)

url = "https://api-akm.goodreels.com/hwycclientreels/chapter/list"
timestamp = str(int(time.time() * 1000))

headers = {
    'authorization': auth_token,
    'user-agent': 'okhttp/4.10.0',
    'content-type': 'application/json; charset=UTF-8'
}

data = {"bookId": "31001045572"}

print(f"POST {url}?timestamp={timestamp}")
print(f"Data: {data}\n")

try:
    resp = requests.post(url, headers=headers, params={'timestamp': timestamp}, json=data, timeout=15)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        print("\n✅ SUCCESS! No signing needed!\n")
        result = resp.json()
        if result.get('data'):
            chapters = result['data'].get('chapters', [])
            print(f"Got {len(chapters)} chapters")
            if chapters:
                print(f"First chapter: {chapters[0].get('title', 'N/A')}")
    else:
        print(f"\n❌ Failed: {resp.status_code}")
        print(resp.text[:300])
        
        # Check error
        if 'sign' in resp.text.lower():
            print("\n⚠️  Error mentions signing - it's REQUIRED")

except Exception as e:
    print(f"Error: {e}")

# Test 2: Reader init
print("\n" + "="*60)
print("TEST: /hwycclientreels/reader/init")
print("="*60)

url = "https://api-akm.goodreels.com/hwycclientreels/reader/init"
timestamp = str(int(time.time() * 1000))

data = {
    "bookId": "31001045572",
    "chapterId": 12989152
}

print(f"POST {url}?timestamp={timestamp}")
print(f"Data: {data}\n")

try:
    resp = requests.post(url, headers=headers, params={'timestamp': timestamp}, json=data, timeout=15)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        print("\n✅ SUCCESS!\n")
        result = resp.json()
        print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
    else:
        print(f"\n❌ Failed: {resp.status_code}")
        print(resp.text[:300])

except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60)
print("CONCLUSION")
print("="*60)
