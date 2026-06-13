import requests
import re
import urllib3

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

url = 'https://vidrama.asia/provider/idrama2'
print(f"Fetching provider page HTML: {url}...")
r = requests.get(url, headers=headers, verify=False)
if r.ok:
    print(f"Downloaded {len(r.text)} chars.")
    
    # Extract Next.js push payloads
    payload_parts = []
    for match in re.finditer(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', r.text):
        part = match.group(1).replace('\\"', '"').replace('\\\\', '\\').replace('\\/', '/')
        payload_parts.append(part)
    
    full_payload = "".join(payload_parts)
    print("Provider payload length:", len(full_payload))
    
    with open('scratch/provider_payload.txt', 'w', encoding='utf-8') as f:
        f.write(full_payload)
    print("Saved provider payload to scratch/provider_payload.txt")
    
    # Check if "serigala" or "161004641891" is in the payload
    for keyword in ["serigala", "161004641891"]:
        matches = [m.start() for m in re.finditer(re.escape(keyword), full_payload, re.IGNORECASE)]
        print(f"Keyword '{keyword}' found {len(matches)} times.")
        for pos in matches[:3]:
            print(f"  Context: {full_payload[max(0, pos-100):min(len(full_payload), pos+150)]}")
else:
    print("Failed to fetch provider page status code:", r.status_code)
