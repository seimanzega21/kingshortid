# -*- coding: utf-8 -*-
import re, sys

sys.stdout.reconfigure(encoding='utf-8')

with open('rsc_combined.txt', 'r', encoding='utf-8') as f:
    text = f.read()

print("Length of RSC text:", len(text))

# Search for potential api URLs or endpoints
matches = re.findall(r'/[a-zA-Z0-9_\-\/]+api[a-zA-Z0-9_\-\/]*', text)
print("\nFound API-like strings in RSC:")
print(set(matches))

# Let's search for melolov3 specifically
melolo_matches = []
for line in text.split('\n'):
    if 'melolo' in line or 'provider' in line:
        melolo_matches.append(line[:120])
print(f"\nFound {len(melolo_matches)} lines with 'melolo' or 'provider':")
for m in melolo_matches[:15]:
    print("  ", m)
