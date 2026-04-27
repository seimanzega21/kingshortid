import requests, json
import os

env_path = r'd:\kingshortid\cf-backend\.env.production'
env_vars = {}
with open(env_path, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, val = line.split('=', 1)
            env_vars[key.strip()] = val.strip().strip('"').strip("'")

admin_key = env_vars.get('ADMIN_API_KEY')

url = 'https://api.shortlovers.id/api/admin/system/delete-small-dramas'
headers = {
    'x-admin-key': admin_key
}

try:
    print('Calling delete endpoint...')
    r = requests.post(url, headers=headers, timeout=60)
    print(r.status_code)
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print('Error:', e)
