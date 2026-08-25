import re, requests
url = 'https://vidrama.asia/movie/dijulukisang-pembangkit-negara--843859?provider=shortmax&lang=id'
html = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}).text
chunks = re.findall(r'src="(/_next/static/chunks/[^"]+\.js)"', html)
for c in chunks:
    print(c)
    js = requests.get('https://vidrama.asia' + c).text
    actions = re.findall(r'([a-f0-9]{40})', js)
    for a in set(actions): print('  Action:', a)
