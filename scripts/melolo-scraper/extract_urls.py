import requests, re
with open('d:/kingshortid/scripts/melolo-scraper/shortmax_watch.html', 'r', encoding='utf-8') as f:
    html = f.read()

js_urls = re.findall(r'\"(/_next/static/chunks/[^\"]+\.js)\"', html)
js_urls = list(set(js_urls))

urls = set()
for js in js_urls:
    try:
        text = requests.get('https://vidrama.asia' + js).text
        found = re.findall(r'https?://[a-zA-Z0-9_\.\-]+[a-zA-Z0-9_\.\-\/]*', text)
        for u in found:
            urls.add(u)
    except Exception as e:
        pass

for u in sorted(list(urls)):
    if 'next' not in u and 'w3.org' not in u and 'reactjs' not in u:
        print(u)
