import requests

url = "https://vidrama.asia/api/melolov3/multi-video?id=7664444328231586869&lang=id"
headers = {"Referer": "https://vidrama.asia/"}
try:
    response = requests.get(url, headers=headers)
    data = response.json()
    total = data.get("total", 0)
    print(f"Total episodes: {total}")
    
    if total > 0:
        first_ep = data["episodes"][0]
        last_ep = data["episodes"][-1]
        
        print(f"Ep {first_ep.get('index')}: has_stream_url={'stream_url' in first_ep}")
        print(f"Ep {last_ep.get('index')}: has_stream_url={'stream_url' in last_ep}")
        if 'stream_url' in last_ep:
            print(f"Last Ep Stream URL preview: {last_ep['stream_url'][:80]}...")
except Exception as e:
    print("Error:", e)
