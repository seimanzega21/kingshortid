import re
import json

with open('test_shortmax.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Check for Next.js app router blobs
app_blobs = re.findall(r'self\.__next_f\.push\(\[(.*?)\]\)', html, re.DOTALL)
print(f"Found {len(app_blobs)} App Router blobs.")

# Let's inspect scripts
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for i, s in enumerate(scripts):
    if '864494' in s:
        print(f"Script {i} has 864494! Length: {len(s)}")
        # Save this script
        with open(f"script_{i}.txt", "w", encoding="utf-8") as sf:
            sf.write(s)

# Check watch hrefs
watch_links = re.findall(r'/watch/[^"\'\s<>]+', html)
print(f"Found {len(watch_links)} watch links.")
if watch_links:
    print("Sample watch links:")
    for wl in watch_links[:10]:
        print(" ", wl)

# Search any API paths
api_paths = re.findall(r'/api/[a-zA-Z0-9_\-\?&=/]+', html)
print(f"Found {len(set(api_paths))} unique api paths:")
for ap in set(api_paths):
    print(" ", ap)
