import requests

try:
    for page in range(1, 10):
        url = f'https://vidrama.asia/api/microdrama?action=list&lang=id&page={page}'
        r = requests.get(url, timeout=30)
        data = r.json()
        dramas = data.get('data', [])
        if not dramas:
            break
        for d in dramas:
            eps = d.get('episodes')
            if eps == 1 or 'Cemburu' in d.get('title', ''):
                print(f"ID: {d['id']} | Title: {d['title']} | Episodes: {eps}")
except Exception as e:
    print(e)
