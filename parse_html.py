# -*- coding: utf-8 -*-
import re, sys, json
sys.stdout.reconfigure(encoding='utf-8')

content = open('temp_watchpage.html', 'r', encoding='utf-8', errors='replace').read()

# Look for og: meta tags
og_title = re.search(r'<meta property="og:title" content="([^"]+)"', content)
og_desc = re.search(r'<meta property="og:description" content="([^"]+)"', content)
og_image = re.search(r'<meta property="og:image" content="([^"]+)"', content)

print("OG Title:", og_title.group(1) if og_title else "NOT FOUND")
print("OG Desc:", og_desc.group(1)[:300] if og_desc else "NOT FOUND")
print("OG Image:", og_image.group(1) if og_image else "NOT FOUND")

# Look for structured data
ld = re.search(r'<script type="application/ld\+json">(.+?)</script>', content, re.DOTALL)
if ld:
    print("\nJSON-LD:")
    print(ld.group(1)[:1000])

# Search for bookName and related
for key in ['bookName', 'totalEpisode', 'totalChapter', 'chapNum', 'chapCount', 'seriesName']:
    matches = re.findall(f'"{key}":"?([^",]+)"?', content)
    if matches:
        print(f"{key}:", matches[:3])
