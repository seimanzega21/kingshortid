# Alternative: Extract Signing Details from HAR

import json
from pathlib import Path
from collections import defaultdict
import base64

har_file = Path("har_files/batch_01.har")

print("Extracting signature patterns from HAR...\n")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

signatures = []
url_patterns = defaultdict(list)

for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    if 'goodreels.com' in url:
        headers = {h['name']: h['value'] for h in entry['request'].get('headers', [])}
        
        if 'sign' in headers or 'Sign' in headers:
            sign_value = headers.get('sign', headers.get('Sign', ''))
            
            # Extract URL path
            path = url.split('?')[0].split('.com')[-1]
            
            # Get timestamp from query or data
            query_params = {p['name']: p['value'] for p in entry['request'].get('queryString', [])}
            timestamp = query_params.get('timestamp', '')
            
            # Get POST data
            post_data = entry['request'].get('postData', {}).get('text', '')
            
            signature_info = {
                'url_path': path,
                'timestamp': timestamp,
                'sign': sign_value,
                'sign_length': len(sign_value),
                'post_data': post_data[:100] if post_data else None,
                'method': entry['request'].get('method', 'GET')
            }
            
            signatures.append(signature_info)
            url_patterns[path].append(sign_value)

print(f"Found {len(signatures)} requests with 'sign' header\n")

# Analyze patterns
print("="*70)
print("SIGNATURE ANALYSIS")
print("="*70)

# Group by endpoint
print("\nSignatures by endpoint:")
for path, signs in url_patterns.items():
    print(f"\n  {path}")
    print(f"    Total requests: {len(signs)}")
    print(f"    Unique signatures: {len(set(signs))}")
    print(f"    Sample signature: {signs[0][:80]}...")

# Check if signatures are unique or reused
all_signs = [s['sign'] for s in signatures]
unique_signs = set(all_signs)

print(f"\n\nTotal signatures: {len(all_signs)}")
print(f"Unique signatures: {len(unique_signs)}")

if len(unique_signs) == len(all_signs):
    print("✅ Each request has UNIQUE signature (request-specific signing)")
else:
    print("⚠️  Some signatures are REUSED (might be token-based)")

# Analyze signature format
if signatures:
    sample = signatures[0]
    print(f"\n\nSample Signature Details:")
    print(f"  URL: {sample['url_path']}")
    print(f"  Timestamp: {sample['timestamp']}")
    print(f"  Sign: {sample['sign'][:80]}...")
    print(f"  Sign length: {sample['sign_length']}")
    print(f"  Method: {sample['method']}")
    if sample['post_data']:
        print(f"  POST data: {sample['post_data']}")
    
    # Try to detect encoding
    try:
        decoded = base64.b64decode(sample['sign'])
        print(f"  ✅ Sign is BASE64 encoded ({len(decoded)} bytes)")
    except:
        print(f"  ❌ Sign is NOT base64 (might be hex or custom encoding)")

# Save signatures to file for analysis
output_file = Path("signature_analysis.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(signatures, f, indent=2, ensure_ascii=False)

print(f"\n\n✅ Saved {len(signatures)} signatures to {output_file}")
print("\nNext steps:")
print("  1. Use Frida to hook signing function (run: run_signature_hook.bat)")
print("  2. Or analyze signature_analysis.json to find patterns")
print("  3. Implement signature generation algorithm")
