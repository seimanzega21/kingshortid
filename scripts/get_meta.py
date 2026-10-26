import requests
import json
import re

url = 'https://www.dracinema.com/movie/harta-karun-dari-sungai-1-ml_7697132717099650101'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=15)
print('Status:', r.status_code)
if r.ok:
    for m in re.finditer(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)', r.text):
        chunk = m.group(1).encode('utf-8').decode('unicode_escape', errors='ignore')
        if 'Alur Harta Karun' in chunk or 'Serangan balik' in chunk:
            print('--- MATCH ---')
            print(chunk)

