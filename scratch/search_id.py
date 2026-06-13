with open("scratch/next_payload.txt", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'25725740830379044', text)]
print(f"Found 25725740830379044 {len(matches)} times.")
for pos in matches:
    print(f"Context: {text[max(0, pos-150):min(len(text), pos+150)]}")
