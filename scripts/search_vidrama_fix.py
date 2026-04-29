import requests
WEB_HDRS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://vidrama.asia/'}
r = requests.get('https://vidrama.asia/api/movie/global_list?lang=id_ID&page=1&limit=20&keyword=Membalas+Semuanya', headers=WEB_HDRS)
if r.ok:
    data = r.json()
    items = data.get('data', {}).get('list', [])
    for it in items:
        print(f"Title: {it.get('title')}, MovieID: {it.get('movieId')}, Provider: {it.get('provider')}")
