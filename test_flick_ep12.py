import requests, urllib3, re
urllib3.disable_warnings()

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

cookie = re.search(r'\'cookie\':\s*\'([^\']+)\'', text).group(1)
headers = {'cookie': cookie, 'referer': 'https://vidrama.asia/'}
url = 'https://vidrama.asia/api/proxy-flickreelsv2?action=chapters&playletId=9515&lang=id'
r = requests.get(url, headers=headers, verify=False)
data = r.json().get('data', {}).get('list', [])

print(f"Total items: {len(data)}")
if len(data) > 0:
    for ep in data:
        print(f"EP {ep['chapter_num']}: hls_url={ep.get('hls_url')} is_locked={ep.get('is_locked')}")
