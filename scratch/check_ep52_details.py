# -*- coding: utf-8 -*-
import requests

sub_url = "https://video-v6.mydramawave.com/vt/19868/2edeb5cb-f848-4acd-a19a-fd93fa26d158.srt"
print("Downloading subtitle...")
try:
    r = requests.get(sub_url, headers={'Referer': 'https://mydramawave.com/'})
    print("Status:", r.status_code)
    print("Content snippet:")
    print(r.text[:300])
except Exception as e:
    print("Error:", e)
