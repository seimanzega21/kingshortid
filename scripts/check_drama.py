import os
import json
import urllib.request
import urllib.parse

# Read env manually
env_path = r'd:\kingshortid\cf-backend\.env.production'
env_vars = {}
with open(env_path, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, val = line.split('=', 1)
            env_vars[key.strip()] = val.strip().strip('"').strip("'")

admin_key = env_vars.get('ADMIN_API_KEY')

headers = {
    'x-admin-key': admin_key
}

drama_id = 'yzj2ccebx7ndri7wnysj8ws4'

req = urllib.request.Request(f"https://api.shortlovers.id/api/admin/dramas/{drama_id}", headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        drama_data = json.loads(response.read().decode())
        print('Drama Details:', json.dumps(drama_data, indent=2))
except Exception as e:
    print('Error fetching drama:', e)
