import requests
import json

url = "https://vidrama.asia/api/microdrama?action=list&lang=id&limit=5"
r = requests.get(url, timeout=20)
if r.ok:
    dramas = r.json().get("dramas", [])
    if dramas:
        print("First drama fields:")
        print(json.dumps(dramas[0], indent=2))
    else:
        print("No dramas returned in list")
else:
    print(f"Failed to fetch list: {r.status_code}")
