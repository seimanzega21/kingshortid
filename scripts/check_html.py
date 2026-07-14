import re
import json

with open('dramaboxa_page.html', encoding='utf-8') as f:
    html = f.read()
    
m3u8 = re.findall(r'(https?://[^\s\"\'>]+\.m3u8[^\s\"\'>]*)', html)
print('M3U8 URLs:', list(set(m3u8)))

# Find any Next.js JSON blobs
jsons = re.findall(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
if jsons:
    data = json.loads(jsons[0])
    print("Found NEXT_DATA!")
    with open("next_data.json", "w", encoding="utf-8") as out:
        json.dump(data, out, indent=2)
    print("Saved to next_data.json")
    
# Find the new self.__next_f.push blobs (App router)
app_blobs = re.findall(r'self\.__next_f\.push\(\[(.*?)\]\)', html)
if app_blobs:
    print(f"Found {len(app_blobs)} App Router blobs.")
    with open("app_blobs.txt", "w", encoding="utf-8") as out:
        for b in app_blobs:
            out.write(b + "\n")
    print("Saved to app_blobs.txt")
