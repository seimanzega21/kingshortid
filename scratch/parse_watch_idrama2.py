import re

with open('scratch/vidrama_watch.html', encoding='utf-8') as f:
    html = f.read()

# Look for .m3u8 urls
matches = re.findall(r'https?://[^\s\"\'\>]+?m3u8[^\s\"\'\>\\]*', html)
print("m3u8 URLs found:", set(matches))

# Look for idrama2 specific URLs
idrama_matches = re.findall(r'https?://[^\s\"\'\>]+?idrama2[^\s\"\'\>\\]*', html)
print("idrama2 URLs found:", set(idrama_matches))

# Also search for 'url' properties in next data
import json
blocks = re.findall(r'\{[^{}]*\}', html)
for b in blocks:
    if 'url' in b.lower() and 'm3u8' in b:
        print("Found block with url:", b)
