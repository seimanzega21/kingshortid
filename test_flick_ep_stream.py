import requests, urllib3, re
urllib3.disable_warnings()

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

cookie = re.search(r'\'cookie\':\s*\'([^\']+)\'', text).group(1)
headers = {'cookie': cookie, 'referer': 'https://vidrama.asia/'}

url_chapters = 'https://vidrama.asia/api/proxy-flickreelsv2?action=chapters&playletId=9515&lang=id'
r_chap = requests.get(url_chapters, headers=headers, verify=False)
chaps = r_chap.json().get('data', {}).get('list', [])

for ep in chaps:
    if ep['chapter_num'] >= 11 and ep['chapter_num'] <= 14:
        chapter_id = ep.get('chapter_id')
        if chapter_id:
            stream_url = f'https://vidrama.asia/api/proxy-flickreelsv2?action=stream&playletId=9515&chapterId={chapter_id}&lang=id'
            r_stream = requests.get(stream_url, headers=headers, verify=False)
            print(f"EP {ep['chapter_num']} stream: {r_stream.status_code} - {r_stream.text[:200]}")
