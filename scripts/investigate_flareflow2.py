import requests
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

html = requests.get('https://vidrama.asia/provider/flareflow', headers={'User-Agent': 'Mozilla/5.0'}, verify=False).text
js_urls = re.findall(r'/_next/static/chunks/[^\"\'\s]+\.js', html)
found = False

for js in set(js_urls):
    js_text = requests.get('https://vidrama.asia' + js, headers={'User-Agent': 'Mozilla/5.0'}, verify=False).text
    if 'flareflow' in js_text.lower():
        print(f'Found flareflow in {js}')
        matches = re.findall(r'https?://[^\s\"\'\\]+', js_text)
        api_urls = set(m for m in matches if 'api' in m or 'vidrama' in m or 'flare' in m)
        if api_urls:
            print('URLs in this JS file:', api_urls)
        found = True
        
if not found:
    print('Not found')
