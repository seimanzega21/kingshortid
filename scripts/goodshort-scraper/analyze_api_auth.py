import json
from pathlib import Path

har_file = Path("har_files/batch_01.har")

print("Analyzing API request headers and authentication...\n")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

# Find a successful /chapter/list request to get headers
for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    if '/hwycclientreels/chapter/list' in url or '/hwycclientreels/book/quick/open' in url:
        request = entry['request']
        
        print(f"📡 Sample API Request:")
        print(f"   URL: {url[:100]}...")
        print(f"   Method: {request.get('method', 'GET')}")
        print(f"\n   Headers:")
        
        headers = request.get('headers', [])
        for header in headers:
            name = header.get('name', '')
            value = header.get('value', '')
            
            # Show important headers
            if name.lower() in ['authorization', 'cookie', 'token', 'sign', 'user-agent', 'content-type', 'x-', 'app-']:
                print(f"      {name}: {value[:80]}{'...' if len(value) > 80 else ''}")
        
        # Check POST data
        post_data = request.get('postData', {})
        if post_data:
            print(f"\n   POST Data:")
            print(f"      {post_data.get('text', '')[:200]}")
        
        # Check query params
        query_params = request.get('queryString', [])
        if query_params:
            print(f"\n   Query Params:")
            for param in query_params[:10]:
                print(f"      {param.get('name', '')}: {param.get('value', '')[:50]}")
        
        print(f"\n{'='*70}\n")
        break  # Just show first one

# Look for chapter/load requests (video URL requests)
print("\nSearching for /chapter/load requests...\n")
load_count = 0
for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    if '/hwycclientreels/chapter/load' in url:
        load_count += 1
        if load_count <= 2:
            request = entry['request']
            print(f"📹 Video Load Request #{load_count}:")
            print(f"   URL: {url[:100]}")
            
            headers = {h['name']: h['value'] for h in request.get('headers', [])}
            if 'sign' in headers or 'Sign' in headers:
                print(f"   ✅ Has 'sign' header")
            if 'token' in headers or 'Token' in headers:
                print(f"   ✅ Has 'token' header")
            
            post_data = request.get('postData', {})
            if post_data:
                try:
                    data = json.loads(post_data.get('text', '{}'))
                    print(f"   POST: {json.dumps(data, ensure_ascii=False)}")
                except:
                    print(f"   POST: {post_data.get('text', '')[:100]}")
            print()

print(f"Total /chapter/load requests found: {load_count}")

if load_count == 0:
    print("\n⚠️  NO chapter/load requests in HAR!")
    print("   This means user did NOT play any videos during capture.")
    print("   Video URLs cannot be fetched without authentication tokens.")
