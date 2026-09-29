import requests
import json

url = "https://vidrama.asia/api/melolov3/multi-video?id=7664444328231586869&lang=id"
headers = {"Referer": "https://vidrama.asia/"}
try:
    response = requests.get(url, headers=headers)
    data = response.json()
    print(data['episodes'][0]['stream_url'])
except Exception as e:
    print("Error:", e)
