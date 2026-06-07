# -*- coding: utf-8 -*-
import requests
import urllib3
import sys
import json
import re
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

scripts = soup.find_all("script")
next_f_content = []

for s in scripts:
    content = s.string if s.string else ""
    if "self.__next_f.push" in content:
        # Extract the string payload
        # self.__next_f.push([1,"..."])
        matches = re.findall(r'self\.__next_f\.push\(\[1,\"(.*)\"\]\)', content)
        for m in matches:
            # Clean up escape sequences
            cleaned = m.encode().decode('unicode-escape', errors='ignore')
            next_f_content.append(cleaned)

full_payload = "".join(next_f_content)
print(f"Total Next_f payload length: {len(full_payload)}")

# Save to a file for analysis
with open("d:\\kingshortid\\scratch\\dramawave_next_f.txt", "w", encoding="utf-8") as f:
    f.write(full_payload)
print("Saved raw payload to scratch/dramawave_next_f.txt")

# Let's search for patterns like movie/ID or titles
# For example, look for /movie/ followed by some chars, or look for title keys
print("\n=== Search for movie link matches in payload ===")
movie_matches = re.findall(r'/movie/[a-zA-Z0-9\-]+', full_payload)
print(f"Found {len(set(movie_matches))} unique movie links:")
for m in sorted(list(set(movie_matches)))[:10]:
    print("  ", m)

# Let's find some titles or series names
print("\n=== Sample text snippets containing title-like structures ===")
titles = re.findall(r'\"title\":\"([^\"]+)\"', full_payload)
print(f"Found {len(set(titles))} unique titles in JSON properties:")
for t in list(set(titles))[:15]:
    print("  ", t)
