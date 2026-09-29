
import requests
res = requests.get('https://api.shortlovers.id/api/dramas?limit=5&includeInactive=true')
print(res.status_code)
print(res.json())

