# -*- coding: utf-8 -*-
import requests

url = "https://stream.shortlovers.id/dramas/cinta-dan-tombak-purba/cover.jpg"
print("Querying R2 cover URL:", url)
try:
    r = requests.get(url, timeout=10)
    print("Status:", r.status_code)
    print("Content-Type:", r.headers.get('Content-Type'))
    print("Content-Length:", len(r.content))
    print("Magic bytes:", r.content[:10])
except Exception as e:
    print("Error:", e)
