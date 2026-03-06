import json
from pathlib import Path

har_file = Path("har_files/batch_01.har")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

print("Sampling actual API response data...\n")

# Sample /chapter/list response
for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    if '/hwycclientreels/chapter/list' in url:
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        if text:
            try:
                data = json.loads(text)
                print("=== CHAPTER LIST RESPONSE ===")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
                break
            except:
                pass

# Sample book/recommend response  
for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    if '/hwycclientreels/book/recommend' in url or '/hwycclientreels/home/index' in url:
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        if text:
            try:
                data = json.loads(text)
                print("\n\n=== BOOK/HOME RESPONSE ===")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
                break
            except:
                pass
