import requests, re
r = requests.get('https://vidrama.asia/provider/idrama')
js_urls = re.findall(r'src="(/_next/static/chunks/[^"]+\.js)"', r.text)
keys = set()
for url in js_urls:
    try:
        js = requests.get('https://vidrama.asia' + url).text
        # match typical Supabase anon keys (ey...)
        keys.update(re.findall(r'ey[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', js))
    except:
        pass
print('Possible JWTs/Keys:', keys)
