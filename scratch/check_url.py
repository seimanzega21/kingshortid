import requests

url = "https://vidrama.asia/api/melolov3/multi-video?id=7664444328231586869&lang=id"
headers = {"Referer": "https://vidrama.asia/"}
try:
    response = requests.get(url, headers=headers)
    print("Status Code:", response.status_code)
    print("Response Content:")
    print(response.text[:1000]) # Print first 1000 chars
except Exception as e:
    print("Error:", e)
