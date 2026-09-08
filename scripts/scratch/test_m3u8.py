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

body = json.dumps(["864494", 1, "id"])
url = 'https://vidrama.asia/watch/cinta-di-antara-spesies--864494/1?provider=shortmax&lang=id'
r = requests.post(url, headers=headers, data=body, verify=False)
lines = r.text.strip().split('\n')
data = None
for line in lines:
    if line.startswith('1:'):
        data = json.loads(line[2:])
        break

if data:
    q720 = data['qualities'].get('video_720')
    print("Direct 720 m3u8 URL:", q720)

    # Check if we can fetch the m3u8 directly without special headers
    m_res = requests.get(q720, timeout=10)
    print("m3u8 fetch status:", m_res.status_code)
    print("m3u8 content preview:")
    print(m_res.text[:500])
