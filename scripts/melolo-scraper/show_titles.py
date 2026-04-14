import requests
API_LIST_URL  = "https://vidrama.asia/api/microdrama?action=list&lang=id"

try:
    r = requests.get(API_LIST_URL, timeout=10)
    data = r.json()
    dramas = data.get("dramas", [])
    print("NEW DRAMAS FETCHED:")
    for i, d in enumerate(dramas[:8], 1):
        print(f"{i}. {d.get('title')}")
except Exception as e:
    print("Error:", e)
