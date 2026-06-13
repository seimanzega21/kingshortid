with open("scratch/watch_payload.txt", "r", encoding="utf-8") as f:
    text = f.read()

import re

# Look for error or not found context
matches = [m.start() for m in re.finditer(r'error|not found|404', text, re.IGNORECASE)]
print(f"Error occurrences: {len(matches)}")
for pos in matches[:5]:
    print(f"Context around {pos}: {text[max(0, pos-150):min(len(text), pos+150)]}")
