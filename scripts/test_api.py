import requests

API = 'https://api.shortlovers.id'

# Test ping
r = requests.get(f'{API}/api/admin/ping-v2', timeout=10)
print(f'Ping: {r.status_code}')

# Test topup without auth
r2 = requests.post(f'{API}/api/coins/topup', json={'packageId':2000}, timeout=10)
print(f'Topup no auth: {r2.status_code}')
print(f'Body: {r2.text[:200]}')
