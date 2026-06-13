with open("scratch/watch_payload.txt", "r", encoding="utf-8") as f:
    text = f.read()

import re

for keyword in [r'"404"', r'404', 'not be found', 'not found']:
    matches = [m.start() for m in re.finditer(keyword, text, re.IGNORECASE)]
    print(f"\nKeyword: {keyword} found {len(matches)} times.")
    for pos in matches[:3]:
        print(f"  Context: {text[max(0, pos-100):min(len(text), pos+150)]}")
