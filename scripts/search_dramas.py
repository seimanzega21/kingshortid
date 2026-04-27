import requests, json, os

env_path = r'd:\kingshortid\cf-backend\.env.production'
env_vars = {}
with open(env_path, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, val = line.split('=', 1)
            env_vars[key.strip()] = val.strip().strip('"').strip("'")

admin_key = env_vars.get('ADMIN_API_KEY')
headers = {'x-admin-key': admin_key}

def search(query):
    url = f'https://api.shortlovers.id/api/admin/dramas?q={query}' # wait, does admin API have search for dramas?
    # Actually let's fetch all via public api or admin dashboard route!
    pass

# The admin API doesn't have a direct /dramas search endpoint in adminRoute, but public API DOES!
# Wait, public API has `/api/dramas/search?q=xxx`

queries = [
    'Dokter Ajaib Dari Desa',
    'Aku Kaya Dari Giok',
    'Raja Tinju di Balik Gerobak',
    'Kebangkitan Raja Balap',
    'Aku Sungguh Bukan Dewa'
]

for q in queries:
    url = f'https://api.shortlovers.id/api/dramas/search?q={requests.utils.quote(q)}'
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        results = data.get('dramas', [])
        if results:
            d = results[0]
            print(f"FOUND: '{q}' -> ID: {d['id']}, Title: {d['title']}, Eps: {d['totalEpisodes']}, Cover: {d['cover']}")
        else:
            print(f"NOT FOUND: '{q}'")
    except Exception as e:
        print(f"Error searching for {q}: {e}")

