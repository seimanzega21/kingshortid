import requests
import re

url = 'https://vidrama.asia/provider/freereels'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}
r = requests.get(url, headers=headers, verify=False)
html = r.text

print(f"HTML size: {len(html)}")

# Find all occurrences of freereels
matches = re.findall(r'"id":"([^"]+)","title":"([^"]+)","slug":"([^"]+)"', html)
if matches:
    print(f'Found {len(matches)} potential dramas:')
    for m in set(matches):
        print(m)
else:
    print('No matches found.')
