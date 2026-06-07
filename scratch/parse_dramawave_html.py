# -*- coding: utf-8 -*-
import requests
import urllib3
import sys
from bs4 import BeautifulSoup

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = "https://vidrama.asia/provider/dramawave"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

r = requests.get(url, headers=headers, verify=False, timeout=15)
soup = BeautifulSoup(r.text, "html.parser")

print("=== ANCHORS FOUND IN DRAMAWAVE PAGE ===")
anchors = soup.find_all("a", href=True)
count = 0
for a in anchors:
    href = a['href']
    text = a.get_text(strip=True)
    # Filter watch page links or movie page links
    if '/movie/' in href or '/watch/' in href:
        print(f"Text: {text} | Href: {href}")
        count += 1

print(f"\nTotal movie/watch links found: {count}")
