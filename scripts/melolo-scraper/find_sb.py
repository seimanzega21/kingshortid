import requests, re
url = 'https://vidrama.asia/watch/dubbingsopir-taksi-mantan-dewa-balap--846959/?provider=shortmax'
html = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).text
js_urls = re.findall(r'src=\"(/_next/static/chunks/[^\"]+\.js)\"', html)
print('Found chunks:', len(js_urls))
for js in js_urls:
    js_text = requests.get('https://vidrama.asia' + js, headers={'User-Agent': 'Mozilla/5.0'}).text
    urls = re.findall(r'https://([a-z0-9]+)\.supabase\.co', js_text)
    if urls:
        print(f'Found Supabase ID in {js}: {list(set(urls))}')
        keys = re.findall(r'eyJh[\w\.\-]+', js_text)
        print(f'Found keys: {[k[:20]+"..." for k in keys]}')
