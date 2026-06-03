import re

with open('scratch/watch_page_snippet.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("HTML length:", len(html))
print("First 1000 characters:")
print(html[:1000])

# Find script elements
scripts = re.findall(r'<script\s+([^>]*?)>', html)
print(f"\nFound {len(scripts)} scripts tags:")
for i, s in enumerate(scripts[:20]):
    print(f"Script {i}: {s}")

# Find any JSON-like data or script content containing "state" or "window." or "__"
for match in re.finditer(r'<script\b[^>]*>(.*?)</script>', html, re.DOTALL):
    content = match.group(1)
    if "NEXT" in content or "props" in content or "state" in content or "window." in content or "book" in content:
        print(f"\nFound match in script! Length: {len(content)}")
        print(content[:500])
