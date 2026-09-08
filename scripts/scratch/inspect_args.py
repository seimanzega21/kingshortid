import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/'
}

r = requests.get('https://vidrama.asia/_next/static/chunks/43f5bb3acc7e88b0.js', headers=headers, verify=False)
js = r.text

# Find where J and L are defined
# In: let e=er.current||"id",t=(i=await q.getEpisodeUrl(J,L,e)).videoUrl||i.url;
pos = js.find('q.getEpisodeUrl(J,L,e)')
if pos != -1:
    print(js[pos-400:pos+300])
else:
    pos = js.find('q.getEpisodeUrl')
    print(js[pos-200:pos+200])
