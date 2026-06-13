import re
import json

with open("scratch/provider_payload.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Search for any movie/drama titles or links
links = re.findall(r'/movie/[^\s"\'\]]+', text)
print("Found movie links in provider payload:")
for l in sorted(list(set(links))):
    print(l)

# Search for "idrama2" in the payload
matches = [m.start() for m in re.finditer(r'idrama2', text, re.IGNORECASE)]
print(f"\n'idrama2' found {len(matches)} times.")
for pos in matches[:5]:
    print(f"  Context: {text[max(0, pos-100):min(len(text), pos+150)]}")
