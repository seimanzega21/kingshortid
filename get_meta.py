import requests, re
html = requests.get('https://vidrama.asia/movie/dijulukisang-pembangkit-negara--843859?provider=shortmax&lang=id').text
title = re.search(r'<title>(.*?)</title>', html)
desc = re.search(r'name="description" content="(.*?)"', html)
cover = re.search(r'property="og:image" content="(.*?)"', html)
print('TITLE:', title.group(1) if title else 'N/A')
print('DESC:', desc.group(1) if desc else 'N/A')
print('COVER:', cover.group(1) if cover else 'N/A')
