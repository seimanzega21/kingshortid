
import requests
res = requests.get('http://141.11.160.187:3002/api/dramas/y8o6b5ff5tm1h1cq11wy81o7?_t=123')
print(res.status_code)
print(len(res.json().get('episodes', [])))

