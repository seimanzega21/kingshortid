with open("scratch/watch_js/f543ba853a1e59a9.js", "r", encoding="utf-8") as f:
    text = f.read()

import re

# Find occurrences of 'idrama2'
matches = [m.start() for m in re.finditer(r'idrama2', text)]
print(f"Occurrences of idrama2: {len(matches)}")
for pos in matches:
    print("\n--- CONTEXT AROUND IDRAMA2 ---")
    start = max(0, pos - 200)
    end = min(len(text), pos + 6000)
    print(text[start:end])
