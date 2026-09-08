import re
import json

with open('watch_shortmax.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Look for m3u8 or mp4
m3u8 = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html)
mp4 = re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', html)
vtt = re.findall(r'https?://[^\s"\'<>]+\.vtt[^\s"\'<>]*', html)

print(f"M3U8 URLs: {len(m3u8)}")
for u in set(m3u8):
    print("  m3u8:", u)

print(f"MP4 URLs: {len(mp4)}")
for u in set(mp4):
    print("  mp4:", u)

print(f"VTT URLs: {len(vtt)}")
for u in set(vtt):
    print("  vtt:", u)

# Check all next_f blobs
blobs = re.findall(r'self\.__next_f\.push\(\[(.*?)\]\)', html, re.DOTALL)
print(f"Total blobs: {len(blobs)}")
with open('watch_shortmax_blobs.txt', 'w', encoding='utf-8') as f:
    for b in blobs:
        f.write(b + "\n")

# Check if there are API endpoints or video urls in the blobs
for i, b in enumerate(blobs):
    if any(k in b.lower() for k in ['video', 'stream', 'episode', 'play', 'shortmax']):
        print(f"Blob {i} matched keywords, len={len(b)}")
