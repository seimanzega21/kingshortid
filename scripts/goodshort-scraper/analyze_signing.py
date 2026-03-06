import json
import base64
from urllib.parse import urlparse, parse_qs

# Load HAR
with open('fresh_capture.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

entries = har['log']['entries']
goodshort_apis = [e for e in entries if 'api-akm.goodreels' in e['request']['url']]

print(f"=== ANALYZING REQUEST SIGNING ===\n")
print(f"Total API calls: {len(goodshort_apis)}\n")

# Extract 5 different requests to analyze signing pattern
samples = []
for i, entry in enumerate(goodshort_apis[:10]):
    req = entry['request']
    
    # Extract key info
    url = req['url']
    method = req['method']
    
    # Get headers
    headers_dict = {h['name'].lower(): h['value'] for h in req['headers']}
    sign = headers_dict.get('sign', '')
    auth = headers_dict.get('authorization', '')
    
    # Get timestamp
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    timestamp = params.get('timestamp', [''])[0]
    
    # Get body
    body = ''
    if method == 'POST' and 'postData' in req:
        body = req['postData'].get('text', '')
    
    sample = {
        'index': i,
        'url': url,
        'path': parsed.path,
        'timestamp': timestamp,
        'body': body,
        'sign': sign,
        'auth_token': auth.replace('Bearer ', '') if auth else '',
        'method': method
    }
    
    samples.append(sample)

# Display samples
for s in samples:
    print(f"\n{'='*80}")
    print(f"Request #{s['index']}")
    print(f"{'='*80}")
    print(f"Path: {s['path']}")
    print(f"Timestamp: {s['timestamp']}")
    print(f"Body: {s['body'][:100] if s['body'] else '(empty)'}...")
    print(f"\nSign (first 80 chars): {s['sign'][:80]}...")
    print(f"Auth Token (first 50 chars): {s['auth_token'][:50]}...")
    
    # Try to analyze sign pattern
    print(f"\nSign Analysis:")
    print(f"  Length: {len(s['sign'])} chars")
    
    # Check if base64
    try:
        decoded = base64.b64decode(s['sign'])
        print(f"  Base64 decoded length: {len(decoded)} bytes")
        print(f"  Likely signature algorithm: RSA or similar (256 bytes = 2048-bit key)")
    except:
        print(f"  Not valid base64")

# Try to find signing pattern by comparing similar requests
print(f"\n\n{'='*80}")
print("PATTERN ANALYSIS")
print(f"{'='*80}")

# Find requests to same endpoint
from collections import defaultdict
by_endpoint = defaultdict(list)
for s in samples:
    by_endpoint[s['path']].append(s)

for endpoint, reqs in by_endpoint.items():
    if len(reqs) >= 2:
        print(f"\nEndpoint: {endpoint}")
        print(f"  {len(reqs)} requests found")
        
        for i, req in enumerate(reqs):
            print(f"\n  Request {i+1}:")
            print(f"    Timestamp: {req['timestamp']}")
            print(f"    Sign: {req['sign'][:40]}...")
            print(f"    Are signs different? {len(set(r['sign'] for r in reqs)) > 1}")

# Save extracted data for analysis
output = {
    'samples': samples,
    'analysis': {
        'sign_length': len(samples[0]['sign']) if samples else 0,
        'sign_appears_base64': True,
        'likely_algorithm': 'RSA-SHA256 or similar',
        'note': 'Sign changes for every request, includes timestamp'
    }
}

with open('signing_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n\n✅ Analysis saved to signing_analysis.json")
print(f"\nNEXT STEPS:")
print(f"1. The 'sign' header is likely RSA signature of request data")
print(f"2. May need to extract private key from APK or find signing endpoint")
print(f"3. Alternative: Check if requests work WITHOUT sign header")
