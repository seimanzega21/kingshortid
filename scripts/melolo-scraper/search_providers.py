import requests, json

valid_providers = ['dotdrama', 'meloshort', 'microdrama', 'dramabox', 'dramawave', 'starshort']
for p in valid_providers:
    url = f'https://vidrama.asia/api/{p}?action=search&q=sopir taksi'
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if 'dramas' in data and data['dramas']:
            print(f'Found in {p}:', len(data['dramas']))
            for d in data['dramas']:
                print(f"  - {d.get('title')}")
    except:
        pass

# Also try melolo
try:
    url = 'https://vidrama.asia/api/melolo?action=search&keyword=sopir taksi'
    r = requests.get(url, timeout=5)
    data = r.json()
    if 'data' in data and data['data']:
        print('Found in melolo:', len(data['data']))
        for d in data['data']:
            print(f"  - {d.get('title')}")
except:
    pass
