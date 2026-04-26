import requests, re
with open('d:/kingshortid/scripts/melolo-scraper/shortmax_watch.html', 'r', encoding='utf-8') as f:
    html = f.read()

js_urls = re.findall(r'\"(/_next/static/chunks/[^\"]+\.js)\"', html)
js_urls = list(set(js_urls))

for js in js_urls:
    try:
        text = requests.get('https://vidrama.asia' + js).text
        keys = re.findall(r'eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+', text)
        for k in set(keys):
            print(k)
    except:
        pass
