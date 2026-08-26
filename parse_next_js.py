import re

with open('movie.html', encoding='utf-8') as f:
    html = f.read()

# Find the next server data JSON
scripts = re.findall(r'self\.__next_f\.push\(\[\d+,\"(.*?)\"\]\)', html)
for s in scripts:
    s_unescaped = s.encode('utf-8').decode('unicode_escape')
    if 'netshortv2' in s_unescaped or '2089169768653586433' in s_unescaped:
        print("Found matching script chunk:")
        # Let's extract the part that looks like episode data
        eps = re.findall(r'\{[^\}]*?\"episode\"\:[^\}]*?\}', s_unescaped)
        if eps:
            for ep in eps[:10]:
                print(ep)
        
        # also print a snippet of the raw string
        print(s_unescaped[:500])
        print("...")
