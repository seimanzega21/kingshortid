import re
from bs4 import BeautifulSoup

with open("d:\\kingshortid\\scratch\\cubetv_page.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
scripts = soup.find_all("script", src=True)

print("=== Found Next.js Client Scripts ===")
for s in scripts:
    src = s['src']
    if '/_next/static/' in src:
        print(f"Script: {src}")
