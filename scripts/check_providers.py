import requests

for provider in ['idrama', 'goodshort', 'stardusttv', 'dramabox', 'melolov2', 'shortmax', 'dotdrama', 'shortsky', 'fundrama', 'flickshort', 'starshort']:
    for page in range(1, 10):
        url = f'https://vidrama.asia/api/{provider}/feed/{page}?lang=id_ID'
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            data = r.json()
            dramas = data.get('data', []) if isinstance(data.get('data'), list) else data.get('dramas', [])
            if isinstance(data, list): dramas = data
            for d in dramas:
                title = d.get('title', '').lower()
                if 'pedang' in title or 'masakanku' in title or 'robot' in title:
                    print(f'FOUND in {provider}: {d.get("title")} -> {d.get("id")}')
        except Exception as e:
            pass
