import re

with open('watch_865915.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's inspect the entire text for any hash-like strings or references
lines = text.split('\n')
for line in lines:
    if 'OMuXG70cIpx0e2YKF_fG5' in line:
        print("Found OMuXG70cIpx0e2YKF_fG5 line snippet:")
        print(line[:300])

# Look for createServerReference or ServerAction or Action in the whole HTML
matches = re.findall(r'[a-f0-9]{40}', text)
print("40-char hex count:", len(matches))
if matches:
    print("Sample 40-char hex:", matches[:10])
