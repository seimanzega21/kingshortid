"""
Analyze HTTPToolkit capture and extract all drama data
"""
import json
from collections import defaultdict
from pathlib import Path

print("📊 Analyzing HTTPToolkit_2026-02-02_23-24.har...")

with open('HTTPToolkit_2026-02-02_23-24.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

entries = har['log']['entries']

# Filter GoodShort API calls
goodshort_apis = [e for e in entries if 'api-akm.goodreels' in e['request']['url']]

print(f"\n✅ Found {len(goodshort_apis)} GoodShort API calls")

# Group by endpoint
by_endpoint = defaultdict(list)
for e in goodshort_apis:
    path = e['request']['url'].split('?')[0].split('/')[-1]
    by_endpoint[path].append(e)

print("\n📋 API Endpoints:")
for endpoint, reqs in sorted(by_endpoint.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {len(reqs):3d}x  /{endpoint}")

# Extract dramas from chapter/list calls
dramas_found = set()
episodes_count = 0

for entry in goodshort_apis:
    url = entry['request']['url']
    
    # Check for chapter list calls
    if '/chapter/list' in url:
        try:
            resp_text = entry['response']['content'].get('text', '')
            if resp_text:
                data = json.loads(resp_text)
                if 'data' in data and 'list' in data['data']:
                    episodes = data['data']['list']
                    episodes_count += len(episodes)
                    
                    # Extract book ID from request
                    if 'postData' in entry['request']:
                        req_body = json.loads(entry['request']['postData']['text'])
                        book_id = req_body.get('bookId')
                        if book_id:
                            dramas_found.add(book_id)
                            print(f"\n  📚 Drama {book_id}: {len(episodes)} episodes")
        except:
            pass

print(f"\n📊 Summary:")
print(f"  Unique dramas: {len(dramas_found)}")
print(f"  Total episodes captured: {episodes_count}")

# Save book IDs for scraper
with open('captured_dramas.json', 'w') as f:
    json.dump({
        'book_ids': list(dramas_found),
        'total_dramas': len(dramas_found),
        'total_episodes': episodes_count,
        'har_file': 'HTTPToolkit_2026-02-02_23-24.har'
    }, f, indent=2)

print(f"\n✅ Saved to captured_dramas.json")
