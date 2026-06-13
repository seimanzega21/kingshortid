import re
import json

with open("scratch/watch_payload.txt", "r", encoding="utf-8") as f:
    text = f.read()

print("Payload Length:", len(text))

# Search for any occurrences of URLs
urls = re.findall(r'https?://[^\s"\'\\}]+', text)
print("\n--- FOUND URLs (Unique, first 30) ---")
unique_urls = sorted(list(set(urls)))
for u in unique_urls[:30]:
    print(u)

# Search for file extensions
for ext in ['.m3u8', '.mp4', '.vtt', '.srt']:
    matches = [m.start() for m in re.finditer(re.escape(ext), text, re.IGNORECASE)]
    print(f"\nExtension '{ext}' found {len(matches)} times.")
    for pos in matches[:5]:
        print(f"  Context around {pos}: {text[max(0, pos-100):min(len(text), pos+100)]}")

# Search for keywords like "video", "stream", "watch", "episode"
for keyword in ["video", "stream", "watch", "episode", "play", "id_ID"]:
    matches = [m.start() for m in re.finditer(re.escape(keyword), text, re.IGNORECASE)]
    print(f"\nKeyword '{keyword}' found {len(matches)} times.")
    for pos in matches[:3]:
        print(f"  Context around {pos}: {text[max(0, pos-80):min(len(text), pos+150)]}")
