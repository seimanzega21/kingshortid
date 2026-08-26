import re
html = open('watch.html', encoding='utf-8').read()
js = set(re.findall(r'/_next/static/[a-zA-Z0-9_\-\/\.]+\.js', html))
for j in js:
    print(j)
