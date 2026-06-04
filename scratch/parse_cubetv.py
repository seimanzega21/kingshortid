import re
from bs4 import BeautifulSoup

with open("d:\\kingshortid\\scratch\\cubetv_page.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Let's search for drama URLs like /watch/... or /movie/... or similar patterns
# We can search in text, scripts, or anchors
print("=== Search for anchors ===")
anchors = soup.find_all("a", href=True)
watch_links = []
for a in anchors:
    href = a['href']
    text = a.get_text(strip=True)
    if '/watch/' in href:
        watch_links.append((href, text))
        print(f"Anchor Watch Link: {href} | Text: {text}")

print(f"Total watch links: {len(watch_links)}")

print("\n=== Search in Script Tags for JSON ===")
scripts = soup.find_all("script")
for i, s in enumerate(scripts):
    content = s.string if s.string else ""
    if "cubetv" in content or "movie" in content or "watch" in content:
        print(f"Script {i} contains keywords, length={len(content)}")
        # Print first 200 chars of script content to check if it's NEXT_DATA or state
        print(content[:300])
        print("...")
