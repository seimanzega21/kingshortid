import re, json
text = open('payload.txt', encoding='utf-8').read()
try:
    m = re.search(r'\{[^{]*"shortPlayName"[^}]*"list":\[.*?\]\}', text, re.IGNORECASE)
    if m:
        print(m.group(0)[:500])
    else:
        print("Not found")
except Exception as e:
    print(e)
