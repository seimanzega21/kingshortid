import requests
import json
import urllib3
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/watch/cinta-di-antara-spesies--864494/1?provider=shortmax&lang=id',
    'Next-Action': '7081ea77aada73681c85542d033db73abd6689d036',
    'Content-Type': 'text/plain;charset=UTF-8',
    'Accept': 'text/x-component'
}

# Test drama lama (864494) vs drama baru (865915)
for movie_id in ['864494', '865915']:
    body = json.dumps([movie_id, 1, "id"])
    url = f'https://vidrama.asia/watch/dummy--{movie_id}/1?provider=shortmax&lang=id'
    r = requests.post(url, headers=headers, data=body, verify=False)
    print(f"Movie {movie_id} status: {r.status_code}")
    print(f"Movie {movie_id} preview: {r.text[:300]}")
    print("-" * 40)
