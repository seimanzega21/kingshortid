import re

with open('watch_865915.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Build ID
build_ids = re.findall(r'"b":"([^"]+)"', text)
print("Build IDs:", set(build_ids))

# Let's inspect all script tags
scripts = re.findall(r'<script[^>]*src="([^"]+)"', text)
print("Scripts:")
for s in scripts:
    print(" ", s)
