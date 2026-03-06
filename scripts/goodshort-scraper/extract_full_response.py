import json
from pathlib import Path

har_file = Path("har_files/batch_01.har")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

# Get full chapter/list response
for entry in har_data['log']['entries']:
    url = entry['request']['url']
    if '/hwycclientreels/chapter/list' in url:
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        if text:
            try:
                data = json.loads(text)
                
                # Save full response for analysis
                with open('chapter_list_sample.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print("Saved full /chapter/list response to chapter_list_sample.json")
                print(f"\nData structure:")
                print(f"  - Root keys: {list(data.keys())}")
                if 'data' in data:
                    print(f"  - data keys: {list(data['data'].keys()) if isinstance(data['data'], dict) else 'is list'}")
                    if isinstance(data['data'], dict) and 'list' in data['data']:
                        if data['data']['list']:
                            print(f"  - list[0] keys: {list(data['data']['list'][0].keys())}")
                            
                            # Check if bookId exists
                            first_item = data['data']['list'][0]
                            if 'bookId' in first_item:
                                print(f"\n✅ Found bookId: {first_item['bookId']}")
                            
                            # Look for book name/title
                            possible_name_keys = ['name', 'bookName', 'title', 'chapterName']
                            for key in possible_name_keys:
                                if key in first_item:
                                    print(f"✅ Found {key}: {first_item[key]}")
                
                break
            except Exception as e:
                print(f"Error: {e}")
