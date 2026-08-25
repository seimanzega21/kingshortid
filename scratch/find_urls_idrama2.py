html = open('scratch/vidrama_watch.html', encoding='utf-8').read()
results = [x for x in html.replace('\\"', '"').split('"') if 'm3u8' in x.lower() or 'mp4' in x.lower() or 'url' in x.lower()]
# Filter just the ones that look like urls
urls = [u for u in results if 'http' in u]
print("Found potential URLs in HTML:")
for u in set(urls):
    print(" -", u)
