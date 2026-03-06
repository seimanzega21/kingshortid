import json
from pathlib import Path

har_file = Path("har_files/batch_01.har")

print("Loading HAR file...")
with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data['log']['entries']
print(f"Total entries: {len(entries)}\n")

# Check for API calls
api_calls = {}
for entry in entries:
    url = entry['request']['url']
    
    # Group by domain
    if 'goodshort' in url or 'goodnovel' in url:
        domain = url.split('/')[2] if len(url.split('/')) > 2 else 'unknown'
        
        if domain not in api_calls:
            api_calls[domain] = []
        
        # Extract endpoint
        path = '/'.join(url.split('/')[3:])[:100]
        api_calls[domain].append(path)

print("API Calls found:")
for domain, calls in api_calls.items():
    print(f"\n{domain}: {len(calls)} calls")
    unique = set(calls)
    for call in list(unique)[:5]:
        print(f"  - {call}")
