import requests
import urllib3
urllib3.disable_warnings()

url = 'https://vidrama.asia/watch/pahlawan-kecil-yang-misterius--865915/1?provider=shortmax&lang=id'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
print('Status:', r.status_code)
print('Length:', len(r.text))
with open('watch_865915.html', 'w', encoding='utf-8') as f:
    f.write(r.text)
