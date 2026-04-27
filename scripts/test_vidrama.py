import requests, json

url = 'https://vidrama.asia/api/microdrama?action=list&lang=id'
try:
    r = requests.get(url, timeout=30)
    dramas = r.json().get('data', [])
    for d in dramas:
        if 'Cemburu' in d.get('title', ''):
            print('Found:', d['title'], 'ID:', d['id'], 'Episodes:', d.get('episodes'))
            
            detail_url = f"https://vidrama.asia/api/microdrama?action=detail&id={d['id']}"
            dr = requests.get(detail_url, timeout=30).json()
            eps = dr.get('episodes', [])
            print('Actual episodes in detail API:', len(eps))
except Exception as e:
    print(e)
