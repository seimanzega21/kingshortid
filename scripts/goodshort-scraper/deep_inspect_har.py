"""
Deep HAR Analyzer - Manual Inspection
Inspect HAR file to understand API structure better
"""

import json
from pathlib import Path
from collections import defaultdict

HAR_FILE = Path("fresh_capture.har")

print("=" * 80)
print("🔍 DEEP HAR INSPECTION")
print("=" * 80)

# Load HAR
with open(HAR_FILE, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data['log']['entries']
print(f"\n✅ Total Requests: {len(entries)}")

# Categorize URLs
api_requests = []
video_requests = []
image_requests = []
other_requests = []

for entry in entries:
    url = entry['request']['url']
    
    if 'api-akm.goodreels.com' in url or 'api.goodreels.com' in url:
        api_requests.append(entry)
    elif url.endswith('.ts'):
        video_requests.append(entry)
    elif '.jpg' in url or '.png' in url or '.webp' in url:
        image_requests.append(entry)
    else:
        other_requests.append(entry)

print(f"\n📊 REQUEST BREAKDOWN:")
print(f"  • API Requests: {len(api_requests)}")
print(f"  • Video Segments (.ts): {len(video_requests)}")
print(f"  • Image Requests: {len(image_requests)}")
print(f"  • Other Requests: {len(other_requests)}")

# Show API endpoints
print(f"\n📡 API ENDPOINTS FOUND ({len(api_requests)} total):")
api_endpoints = defaultdict(int)
for entry in api_requests:
    url = entry['request']['url']
    # Extract path
    if '?' in url:
        path = url.split('?')[0].split('.com')[-1]
    else:
        path = url.split('.com')[-1]
    
    api_endpoints[path] += 1

for path, count in sorted(api_endpoints.items(), key=lambda x: x[1], reverse=True):
    print(f"  • {path}: {count} calls")

# Show sample API responses
print(f"\n🔍 SAMPLE API RESPONSES:")
print("=" * 80)

sample_count = 0
for entry in api_requests[:20]:  # Check first 20 API calls
    url = entry['request']['url']
    
    try:
        response_text = entry['response']['content'].get('text', '')
        if response_text and len(response_text) > 10:
            sample_count += 1
            print(f"\n--- API CALL {sample_count} ---")
            print(f"URL: {url}")
            print(f"Method: {entry['request']['method']}")
            print(f"Status: {entry['response']['status']}")
            
            # Try to parse JSON
            try:
                data = json.loads(response_text)
                print(f"Response (JSON):")
                # Print first 500 chars
                print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
                print("...")
            except:
                print(f"Response (Text): {response_text[:500]}...")
            
            print("-" * 80)
            
            if sample_count >= 10:  # Only show first 10
                break
    except Exception as e:
        continue

print(f"\n✅ Inspection complete!")
print(f"📁 Check output above for API structure details")
