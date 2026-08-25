import requests
import re
r = requests.get('https://vidrama.asia/movie/balas-budi-ular-suci--2059089132047048706?provider=netshortv2&lang=id', headers={'User-Agent':'Mozilla/5.0'})
with open('debug_vidrama.html', 'w', encoding='utf-8') as f:
    f.write(r.text)
m = re.search(r'"videoUrl":"([^"]+)"', r.text)
print('Video URL from HTML:', m.group(1)) if m else print('Not found in HTML')
