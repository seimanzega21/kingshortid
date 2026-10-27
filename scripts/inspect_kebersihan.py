import requests
import json
import base64
import re

url = 'https://www.dracinema.com/movie/balas-dendam-petugas-kebersihan-sulih-suara-dw_9wHoau6lwv'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=15)
print('Page status:', r.status_code)
if r.ok:
    for m in re.finditer(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)', r.text):
        chunk = m.group(1).encode('utf-8').decode('unicode_escape', errors='ignore')
        if 'schema.org' in chunk and 'TVSeries' in chunk:
            print('Schema:', chunk)
        if 'Alur Balas' in chunk or 'Sinopsis' in chunk:
            print('Sinopsis chunk:', chunk[:400])

# Now check playback API
pb_url = 'https://www.dracinema.com/api/playback'
headers = {
    'Content-Type': 'application/json',
    'X-API-Key': 'xb3MdwdLrZrpaDXvrLLwfP==',
    'User-Agent': 'Mozilla/5.0'
}
movie_key = 'balas-dendam-petugas-kebersihan-sulih-suara-dw_9wHoau6lwv'
r_pb = requests.post(pb_url, headers=headers, json={'movieKey': movie_key, 'episode': 1}, timeout=10)
print('Playback status:', r_pb.status_code)
if r_pb.ok:
    token = r_pb.json().get('token')
    s = token.split('.')[1]
    s += '=' * ((4 - len(s) % 4) % 4)
    data = json.loads(base64.b64decode(s.replace('-', '+').replace('_', '/')).decode('utf-8'))
    print('Playback kind:', data.get('kind'))
    print('Meta:', data.get('data', {}).get('meta'))
    detail = data.get('data', {}).get('detail', {})
    print('Detail keys:', detail.keys())
    print('Video URLs:', detail.get('videoUrls'))
    print('Sub URL:', detail.get('sub'))
    print('Inline subtitle:', bool(data.get('subtitle')))
    if data.get('subtitle'):
        print('Subtitle snippet:', data.get('subtitle')[:200])
