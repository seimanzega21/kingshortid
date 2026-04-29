import requests, json

targets = ['pedang', 'masakanku', 'robot']
found = []

for page in range(1, 15):
    url = f'https://vidrama.asia/api/netshortv2/feed/{page}?lang=id_ID'
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = r.json()
        
        dramas = []
        if 'data' in data and isinstance(data['data'], list):
            dramas = data['data']
        elif 'dramas' in data and isinstance(data['dramas'], list):
            dramas = data['dramas']
        elif isinstance(data, list):
            dramas = data
            
        if not dramas:
            print(f'Page {page}: No dramas found. Data keys: {list(data.keys()) if isinstance(data, dict) else "list"}')
            continue
            
        print(f'Page {page}: found {len(dramas)} dramas')
        for d in dramas:
            title = d.get('title', '').lower()
            for t in targets:
                if t in title:
                    found.append(d)
                    title_text = d.get('title')
                    id_text = d.get('id')
                    print(f'FOUND: {title_text} -> ID: {id_text}')
    except Exception as e:
        print(f"Error on page {page}: {e}")

print(f'Total found: {len(found)}')
open('netshort_targets.json', 'w', encoding='utf-8').write(json.dumps(found, ensure_ascii=False, indent=2))
