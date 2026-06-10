import requests
import json
r = requests.get('https://api.shortlovers.id/api/dramas')
if r.ok:
    data = r.json()
    dramas_list = data if isinstance(data, list) else data.get('dramas', [])
    print('Found', len(dramas_list), 'dramas')
    for d in dramas_list[:3]:
        print(d['title'])
        r2 = requests.get(f"https://api.shortlovers.id/api/dramas/{d['id']}")
        if r2.ok:
            eps = r2.json().get('episodes', [])
            if eps:
                print('  Ep 1 URL:', eps[0].get('videoUrl'))
