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

for ep in [1, 2, 10, 11, 15]:
    body = json.dumps(["864494", ep, "id"])
    url = f'https://vidrama.asia/watch/cinta-di-antara-spesies--864494/{ep}?provider=shortmax&lang=id'
    r = requests.post(url, headers=headers, data=body, verify=False)
    print(f"Episode {ep}: status {r.status_code}")
    lines = r.text.strip().split('\n')
    for line in lines:
        if line.startswith('1:'):
            try:
                data = json.loads(line[2:])
                video_url = data.get('videoUrl')
                qualities = data.get('qualities', {})
                print(f"  videoUrl: {video_url[:80] if video_url else None}")
                print(f"  qualities keys: {list(qualities.keys())}")
            except Exception as e:
                print(f"  parse error: {e}")
