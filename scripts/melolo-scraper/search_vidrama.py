import requests, re, urllib.parse
titles = ['Satu Langkah Menjadi Dewa', 'Legenda yang Terbuang', 'Raja Tinju di Balik Gerobak']
headers = {'User-Agent': 'Mozilla/5.0'}
for title in titles:
    url = f'https://vidrama.asia/search?q={urllib.parse.quote(title)}'
    r = requests.get(url, headers=headers)
    
    # We want to extract links like /movie/satu-langkah-menjadi-dewa--2034897075744800770
    matches = re.findall(r'href="/movie/([^/"\?]+)', r.text)
    
    if not matches:
        # let's try RSC searching
        matches2 = re.findall(r'\"slug\":\"([^\"]+)\",\"id\":\"(\d+)\"', r.text)
        if matches2:
            print(f'FOUND {title}: {matches2}')
        else:
            print(f'NOT FOUND: {title}')
    else:
        unique = list(set(matches))
        print(f'FOUND {title}: {unique}')
