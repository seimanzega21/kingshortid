with open('watch_865915.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'I\[\d+,\[[^\]]+\]', text)
for m in matches[:10]:
    print(m)
