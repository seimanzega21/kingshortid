import json
import re

html = open('debug_vidrama.html', encoding='utf-8').read()
script = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
if script:
    data = json.loads(script.group(1))
    props = data.get('props', {}).get('pageProps', {})
    print(json.dumps(props, indent=2)[:2000])
else:
    print('No NEXT_DATA')
