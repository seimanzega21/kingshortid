import re
html = open('d:/kingshortid/scripts/watch_page.html', encoding='utf-8').read()
print('length:', len(html))
matches = re.findall(r'self\.__next_f\.push\(\[1,\"(.*?)\"\]\)', html)
print('chunks:', len(matches))
for m in matches:
    if 'videos' in m or 'url' in m or 'quality' in m or 'flareflow' in m:
        try:
            s = m.encode('utf-8').decode('unicode_escape')
            if 'videos' in s or 'url' in s:
                print("FOUND in chunk:", s[:500])
        except:
            print("FOUND unparsed:", m[:500])
