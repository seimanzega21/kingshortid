import json
from pathlib import Path
from collections import Counter

har_file = Path("har_files/batch_01.har")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

# Check what endpoints exist
endpoints = []
for entry in har_data['log']['entries']:
    url = entry['request']['url']
    if 'goodreels' in url:
        # Get path
        try:
            parts = url.split('/')
            if len(parts) > 3:
                path = '/' + '/'.join(parts[3:]).split('?')[0]
                endpoints.append(path)
        except:
            pass

endpoint_counts = Counter(endpoints)

print("Top 20 GoodReels endpoints in NEW capture:\n")
for ep, count in endpoint_counts.most_common(20):
    print(f"  {count:3d}  {ep}")

# Sample one response
print("\n\nSample response from /hwycclientreels/chapter/list:\n")
for entry in har_data['log']['entries']:
    url = entry['request']['url']
    if '/hwycclientreels/chapter/list' in url:
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        if text:
            try:
                data = json.loads(text)
                print(json.dumps(data, indent=2, ensure_ascii=False)[:1500])
                break
            except:
                pass
