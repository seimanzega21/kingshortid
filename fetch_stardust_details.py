# -*- coding: utf-8 -*-
import requests, json, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/en/watch/satu-pedang-tebas-raja-neraka--19820/1?provider=stardusttv',
    'Accept': 'text/x-component',
    'Content-Type': 'text/plain;charset=UTF-8',
}

movie_ids = [
    '19716', '19123', '19927', '19804', '19657', '19375', '19954', 
    '19272', '17683', '18867', '19709', '17916', '1313', '19533'
]

results = []

for mid in movie_ids:
    url = f'https://vidrama.asia/en/watch/some-slug--{mid}/1?provider=stardusttv'
    hdrs = WEB_HDRS.copy()
    hdrs['next-action'] = '60ea10e5421e7d8bbba1e0d453714768474e2a8880'
    
    try:
        r = requests.post(url, headers=hdrs, data=json.dumps([mid, "id"]), timeout=15, verify=False)
        if r.ok:
            # Parse Next.js action response format: '1:{"id":"..."}'
            parsed_data = None
            for line in r.text.split('\n'):
                if '"title"' in line:
                    content = line[line.find('{'):] if '{' in line else line
                    parsed_data = json.loads(content)
                    break
            
            if parsed_data:
                title = parsed_data.get('title')
                desc = parsed_data.get('description') or parsed_data.get('introduction')
                cover = parsed_data.get('cover') or parsed_data.get('image')
                genres = parsed_data.get('genres') or ['Drama']
                total_eps = parsed_data.get('totalEpisodes') or parsed_data.get('maxEps') or 60
                
                print(f"ID {mid}:")
                print(f"  Title (original): {parsed_data.get('name')}")
                print(f"  Title (in payload): {title}")
                print(f"  Total Eps: {total_eps}")
                
                results.append({
                    'id': mid,
                    'title': title,
                    'original_title': parsed_data.get('name'),
                    'description': desc,
                    'cover': cover,
                    'genres': genres,
                    'totalEpisodes': total_eps
                })
        else:
            print(f"ID {mid} failed: {r.status_code}")
    except Exception as e:
        print(f"ID {mid} error: {e}")

# Write to a JSON file
with open('stardust_movies_meta.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
