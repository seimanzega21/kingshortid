import requests, re
r = requests.get('https://vidrama.asia/provider/idrama')
js_urls = re.findall(r'src="(/_next/static/chunks/[^"]+\.js)"', r.text)
tables = set()
for url in js_urls:
    try:
        js = requests.get('https://vidrama.asia' + url).text
        matches = re.findall(r'\.from\([\"\'\`]+([a-zA-Z0-9_]+)[\"\'\`]+\)', js)
        tables.update(matches)
    except Exception as e:
        pass
print('Tables found in JS:', tables)
