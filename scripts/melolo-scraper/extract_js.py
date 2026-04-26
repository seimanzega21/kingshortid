import requests, re
with open('d:/kingshortid/scripts/melolo-scraper/shortmax_watch.html', 'r', encoding='utf-8') as f:
    html = f.read()

js_urls = re.findall(r'\"(/_next/static/chunks/[^\"]+\.js)\"', html)
js_urls = list(set(js_urls))
print(f'Found {len(js_urls)} JS files.')

api_routes = set()
for url in js_urls:
    try:
        text = requests.get('https://vidrama.asia' + url).text
        apis = re.findall(r'/api/[a-zA-Z0-9_\-]+', text)
        for api in apis:
            api_routes.add(api)
    except Exception as e:
        print(f"Error {url}: {e}")

print('API Routes found in JS:', list(api_routes))
