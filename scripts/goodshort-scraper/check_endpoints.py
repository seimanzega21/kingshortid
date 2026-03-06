import json
from pathlib import Path

har_file = Path("har_files/batch_01.har")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

print("Looking for goodreels API endpoints...\n")

endpoints = set()
for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    if 'goodreels' in url:
        # Extract path
        parts = url.split('/')
        if len(parts) > 3:
            # Get paths after domain
            path = '/' + '/'.join([p for p in parts[3:] if p and not p.startswith('?')])
            # Strip query params
            path = path.split('?')[0]
            endpoints.add(path)

print(f"Found {len(endpoints)} unique goodreels endpoints:\n")
for ep in sorted(endpoints)[:30]:
    print(f"  {ep}")
