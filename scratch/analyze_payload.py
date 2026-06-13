import re

with open('scratch/next_payload.txt', 'r', encoding='utf-8') as f:
    text = f.read()

print("File size:", len(text))

# Let's search for some keys
search_keys = ['id', 'title', 'cover', 'description', 'episodes', 'video', 'url', 'm3u8', 'mp4', 'subtitle', 'vtt', 'provider']
for key in search_keys:
    # Find positions of matches
    matches = [m.start() for m in re.finditer(r'\b' + re.escape(key) + r'\b', text, re.IGNORECASE)]
    print(f"Key '{key}': found {len(matches)} times. Positions: {matches[:5]}")

# Let's print sections around the first few occurrences of 'id' or 'title' or 'provider'
for m in re.finditer(r'provider', text, re.IGNORECASE):
    pos = m.start()
    print("\n--- AROUND PROVIDER ---")
    print(text[max(0, pos-100):min(len(text), pos+300)])

for m in re.finditer(r'\"id\"', text):
    pos = m.start()
    print("\n--- AROUND ID ---")
    print(text[max(0, pos-100):min(len(text), pos+300)])
