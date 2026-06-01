import requests, json

url = "https://vidrama.asia/api/microdrama?action=list&lang=id&limit=2"
print(f"Requesting: {url}")
r = requests.get(url, timeout=20)
if r.ok:
    data = r.json()
    dramas = data.get("dramas", [])
    print(f"Total dramas in list: {len(dramas)}")
    if dramas:
        print("\nFirst drama in list keys and values:")
        for k, v in dramas[0].items():
            print(f"  {k}: {str(v)[:300]}")
else:
    print(f"Error: {r.status_code}")
