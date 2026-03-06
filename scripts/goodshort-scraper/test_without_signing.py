"""
Test API requests WITHOUT signing
Try to make simple requests to see if signing is actually required
"""

import requests
import json
import time

def test_unsigned_request():
    """Try making API request without signature"""
    
    # Extract token from HAR
    har_file = "HTTPToolkit_2026-02-03_00-53.har"
    
    with open(har_file, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    # Find a request with auth token
    auth_token = None
    for entry in har['log']['entries']:
        for header in entry['request']['headers']:
            if header['name'].lower() == 'authorization':
                auth_token = header['value']
                break
        if auth_token:
            break
    
    if not auth_token:
        print("❌ No auth token found in HAR")
        return
    
    print(f"✅ Found auth token: {auth_token[:50]}...\n")
    
    # Test 1: Simple GET request (list dramas)
    print("="*80)
    print("TEST 1: GET request WITHOUT signing")
    print("="*80 + "\n")
    
    url = "https://api-akm.goodreels.com/hwycclientreels/book/shelf/allList"
    timestamp = str(int(time.time() * 1000))
    
    headers = {
        'authorization': auth_token,
        'user-agent': 'okhttp/4.10.0',
        'accept': 'application/json'
    }
    
    params = {
        'timestamp': timestamp
    }
    
    print(f"URL: {url}")
    print(f"Timestamp: {timestamp}")
    print(f"Auth: {auth_token[:50]}...")
    print("\nMaking request WITHOUT sign header...\n")
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"Status: {resp.status_code}")
        print(f"Response length: {len(resp.text)} bytes")
        
        if resp.status_code == 200:
            print("\n✅ SUCCESS! Signing might not be required!\n")
            data = resp.json()
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
        else:
            print(f"\n❌ Failed: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: POST request
    print("\n" + "="*80)
    print("TEST 2: POST request WITHOUT signing - Get drama detail")
    print("="*80 + "\n")
    
    url = "https://api-akm.goodreels.com/hwycclientreels/book/detail"
    timestamp = str(int(time.time() * 1000))
    
    headers = {
        'authorization': auth_token,
        'user-agent': 'okhttp/4.10.0',
        'content-type': 'application/json; charset=UTF-8'
    }
    
    params = {
        'timestamp': timestamp
    }
    
    data = {
        "bookId": "31001045572"  # Our test drama
    }
    
    print(f"URL: {url}")
    print(f"Data: {data}")
    print("\nMaking POST request WITHOUT sign header...\n")
    
    try:
        resp = requests.post(url, headers=headers, params=params, json=data, timeout=15)
        print(f"Status: {resp.status_code}")
        print(f"Response length: {len(resp.text)} bytes")
        
        if resp.status_code == 200:
            print("\n✅ SUCCESS! Signing NOT required for this endpoint!\n")
            result = resp.json()
            
            if result.get('data'):
                book_data = result['data']
                print(f"Title: {book_data.get('title', 'N/A')}")
                print(f"Author: {book_data.get('author', 'N/A')}")
                print(f"Episodes: {len(book_data.get('chapters',  []))}")
        else:
            print(f"\n❌ Failed: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
            
            # Check if error mentions signature
            if 'sign' in resp.text.lower() or 'signature' in resp.text.lower():
                print("\n⚠️  Error mentions 'sign' - signing IS required")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Home feed (where we got covers)
    print("\n" + "="*80)
    print("TEST 3: Home feed request")
    print("="*80 + "\n")
    
    url = "https://api-akm.goodreels.com/hwycclientreels/channel/home"
    timestamp = str(int(time.time() * 1000))
    
    headers = {
        'authorization': auth_token,
        'user-agent': 'okhttp/4.10.0',
        'content-type': 'application/json; charset=UTF-8'
    }
    
    params = {
        'timestamp': timestamp
    }
    
    data = {}
    
    print(f"URL: {url}")
    print("\nMaking request WITHOUT sign header...\n")
    
    try:
        resp = requests.post(url, headers=headers, params=params, json=data, timeout=15)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            print("\n✅ Home feed works without signing!")
            result = resp.json()
            if result.get('data', {}).get('list'):
                dramas = result['data']['list'][:3]
                print(f"\nGot {len(dramas)} dramas:")
                for drama in dramas:
                    print(f"  - {drama.get('title', 'N/A')}")
        else:
            print(f"\n❌ Failed: {resp.status_code}")
            print(f"Response: {resp.text[:300]}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n🧪 TESTING API WITHOUT SIGNING\n")
    print("This will help us understand if signing is actually required\n")
    test_unsigned_request()
