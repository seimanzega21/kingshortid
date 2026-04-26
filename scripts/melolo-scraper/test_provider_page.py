import requests
import re
import json

url = "https://vidrama.asia/provider/shortmax"
r = requests.get(url)
print(f"Status: {r.status_code}")

# Find any __next_f that contains our drama slug
match = re.search(r'dubbingsopir-taksi-mantan-dewa-balap--846959', r.text)
if match:
    print("Found the target drama on the page!")
else:
    print("Not found on the first page.")

matches = re.finditer(r'\{"id":"[^"]+","title":"[^"]+","poster":"[^"]+"', r.text)
count = 0
for m in matches:
    print(m.group(0))
    count += 1
    if count > 5: break
