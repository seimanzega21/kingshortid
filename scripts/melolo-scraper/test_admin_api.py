import requests, json

r = requests.get('http://localhost:3000/api/dramas?limit=5')
data = r.json()
print(f"Admin panel API returns {data.get('total', 0)} dramas\n")
for d in data.get('dramas', []):
    desc = d.get('description', 'EMPTY')[:80]
    print(f"{d['title'][:40]:40s} | {desc}")
