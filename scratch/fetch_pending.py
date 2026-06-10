import urllib.request
import json
import re

url = 'http://141.11.160.187:8000/rest/v1/dramas?isActive=eq.false&select=id,title,cover'
req = urllib.request.Request(url, headers={'apikey': 'anon_or_service_role', 'Authorization': 'Bearer anon_or_service_role'})

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        
        with open('scratch/pending_dramas.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"Saved {len(data)} pending dramas to scratch/pending_dramas.json")
except Exception as e:
    print('Failed:', e)
