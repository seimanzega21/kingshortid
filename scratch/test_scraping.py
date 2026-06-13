import requests
import re
import urllib3

urllib3.disable_warnings()

url = 'https://vidrama.asia/movie/aku-lahirkan-anak-serigala-presiden--161004641891?provider=idrama2&lang=id'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)

# Next.js App Router uses self.__next_f.push([1, "payload"]) or self.__next_f.push([0, ...])
# Let's extract these blocks
payload_parts = []
for match in re.finditer(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', r.text):
    part = match.group(1)
    # Decode escape sequences
    part = part.replace('\\"', '"').replace('\\\\', '\\').replace('\\/', '/')
    payload_parts.append(part)

full_payload = "".join(payload_parts)
print("Combined payload length:", len(full_payload))

# Write to a file for manual inspection
with open('scratch/next_payload.txt', 'w', encoding='utf-8') as f:
    f.write(full_payload)

# Let's try to find if there are any JSON segments in the payload that look like movie details
# Movie IDs, episode details, player details etc.
ep_ids = re.findall(r'"episodeNo":\s*(\d+)', full_payload)
print("Found episodes:", len(ep_ids), ep_ids[:10])

# Search for cover / images
images = re.findall(r'https://[^"]+?\.(?:jpg|jpeg|png)', full_payload)
print("Found images:", len(images), list(set(images))[:5])
