import requests
r = requests.get('https://vidrama.asia/api/microdrama?action=list&limit=5000')
dramas = r.json().get('dramas', [])
print(f'Total global dramas: {len(dramas)}')
targets = ['pedang', 'masakanku', 'robot']
for d in dramas:
    title = d.get('title', '').lower()
    if any(t in title for t in targets):
        print(f'FOUND: {d.get("title")} -> {d.get("id")}')
