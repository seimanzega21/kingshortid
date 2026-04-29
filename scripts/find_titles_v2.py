import requests

targets = ['pedang', 'masakanku', 'robot']
for page in range(1, 15):
    for provider in ['netshort', 'netshortv2']:
        url = f'https://vidrama.asia/api/{provider}/feed/{page}?lang=id_ID'
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            data = r.json()
            dramas = data.get('data', []) if isinstance(data.get('data'), list) else data.get('dramas', [])
            if isinstance(data, list): dramas = data
            for d in dramas:
                title = d.get('title', '').lower()
                if any(t in title for t in targets):
                    print(f'FOUND in {provider}: {d.get("title")} -> {d.get("id")}')
        except Exception as e:
            pass
