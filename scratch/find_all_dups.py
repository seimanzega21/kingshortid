import urllib.request
import json
import re

def clean_title(t):
    t = t.lower()
    t = re.sub(r'\[versi dub\]|\(sulih suara\)|\[dubbing\]|\[dijuluki\]', '', t)
    return re.sub(r'[^a-z0-9]', '', t)

url = 'http://141.11.160.187:8000/rest/v1/dramas?select=id,title,isActive,status,cover'
req = urllib.request.Request(url, headers={'apikey': 'anon_or_service_role', 'Authorization': 'Bearer anon_or_service_role'})

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        
        seen = {}
        for d in data:
            c = clean_title(d['title'])
            if c in seen:
                seen[c].append(d)
            else:
                seen[c] = [d]
                
        to_delete = []
        
        print(f"Total dramas in DB: {len(data)}")
        print("\n--- DUPLICATES FOUND ---")
        
        for c, arr in seen.items():
            if len(arr) > 1:
                print(f"TITLE: {arr[0]['title']}")
                # If there are multiple, print them all
                for d in arr:
                    status = "ACTIVE" if d.get('isActive') else "PENDING"
                    print(f"  - [{status}] ID: {d['id']}, Cover: {d['cover']}")
                    
                    if not d.get('isActive'):
                        to_delete.append(d)
                        
        print("\n--- TO BE DELETED (PENDING DUPLICATES) ---")
        for d in to_delete:
            print(f"- {d['title']} (ID: {d['id']})")
except Exception as e:
    print('Failed:', e)
