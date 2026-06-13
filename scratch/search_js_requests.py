import os
import re

js_dir = "d:\\kingshortid\\scratch\\js"
files = os.listdir(js_dir)

keywords = [
    r'axios',
    r'\.get\b',
    r'\.post\b',
    r'request\b',
    r'http\b',
    r'fetch',
]

for filename in files:
    if not filename.endswith('.js'):
        continue
    filepath = os.path.join(js_dir, filename)
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    found = []
    for kw in keywords:
        matches = list(re.finditer(kw, content, re.IGNORECASE))
        if matches:
            found.append(f"{kw}: {len(matches)}")
            
    if found:
        print(f"File {filename}: {', '.join(found)}")
        
        # Let's print some sample context for request or fetch
        for kw in [r'request\b', r'fetch']:
            for m in list(re.finditer(kw, content, re.IGNORECASE))[:2]:
                pos = m.start()
                print(f"  [{kw}] Context: {content[max(0, pos-100):min(len(content), pos+150)]}")
