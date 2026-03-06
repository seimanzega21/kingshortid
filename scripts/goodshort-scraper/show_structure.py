import json
from pathlib import Path

har_file = Path("har_files/batch_01.har")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    if '/hwycclientreels/chapter/list' in url:
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        if text:
            try:
                data = json.loads(text)
                if data.get('data', {}).get('list'):
                    book = data['data']['list'][0]
                    print("ACTUAL BOOK STRUCTURE:")
                    print(json.dumps(book, indent=2, ensure_ascii=False)[:3000])
                    break
            except:
                pass
