
import requests
res = requests.get('https://api.shortlovers.id/api/dramas/y8o6b5ff5tm1n1cq11wy81o7?includeInactive=true')
print(res.status_code)
print(res.text)

