import requests
WEB_HDRS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://vidrama.asia/'}
for p in range(1, 5):
    r = requests.get(f'https://vidrama.asia/api/movie/global_list?lang=id_ID&page={p}&limit=100&keyword=Putri', headers=WEB_HDRS)
    if r.ok:
        data = r.json()
        items = data.get('data', {}).get('list', [])
        for it in items:
            title = it.get('title', '')
            if 'Asli' in title or 'Kembali' in title:
                print(f"Title: {title}, MovieID: {it.get('movieId')}, Provider: {it.get('provider')}")
    else:
        print(f"Error page {p}: {r.status_code}")
