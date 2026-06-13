import requests
import re
import urllib3

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

url = 'https://vidrama.asia/watch/aku-lahirkan-anak-serigala-presiden--161004641891/1?provider=idrama2&lang=id'
print(f"Fetching watch page HTML: {url}...")
r = requests.get(url, headers=headers, verify=False)
if r.ok:
    print(f"Downloaded {len(r.text)} chars.")
    
    # Extract Next.js push payloads
    payload_parts = []
    for match in re.finditer(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', r.text):
        part = match.group(1)
        part = part.replace('\\"', '"').replace('\\\\', '\\').replace('\\/', '/')
        payload_parts.append(part)
    
    full_payload = "".join(payload_parts)
    print("Watch Combined payload length:", len(full_payload))
    
    with open('scratch/watch_payload.txt', 'w', encoding='utf-8') as f:
        f.write(full_payload)
    print("Saved watch payload to scratch/watch_payload.txt")
else:
    print("Failed to fetch page status code:", r.status_code)
