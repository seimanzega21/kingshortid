import requests
import re
import urllib3
import sys

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = "https://vidrama.asia/movie/bertani-menjinakkan-dewa-dingin--QZpz60?provider=cubetv&lang=id"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

r = requests.get(url, headers=headers, verify=False, timeout=15)
print("Status:", r.status_code)
if r.ok:
    print("Page Length:", len(r.text))
    # Look for NEXT_DATA or state
    with open("scratch/movie_page_QZpz60.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    print("Saved page to scratch/movie_page_QZpz60.html")
    
    # Search for any references to QZpz60 in text
    matches = re.findall(r'QZpz60', r.text)
    print("Occurrences of 'QZpz60' in HTML:", len(matches))
else:
    print(r.text)
