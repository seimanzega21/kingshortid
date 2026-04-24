import requests
import re
import json

def fetch_drama_data(slug):
    url = f"https://vidrama.asia/{slug}"
    print(f"Fetching {url}")
    r = requests.get(url)
    
    # Next.js App Router RSC data is typically in script tags containing __next_f.push
    matches = re.findall(r'self\.__next_f\.push\(\[(.*?)\)\]\s*</script>', r.text, re.DOTALL)
    
    data_pieces = []
    for m in matches:
        # m is a string like: 1,"some json string"
        try:
            # We wrap it in [] to make it a valid JSON array
            parsed = json.loads(f"[{m})")
            if len(parsed) >= 2 and isinstance(parsed[1], str):
                data_pieces.append(parsed[1])
        except Exception as e:
            pass
            
    # Look for m3u8 or mp4
    links = set()
    for piece in data_pieces:
        links.update(re.findall(r'https?://[^\s\"\']+\.(?:mp4|m3u8)[^\s\"\']*', piece))
        
    print("Found video links:", len(links))
    for link in list(links)[:5]:
        print(" -", link)

fetch_drama_data("tiga-tahun-diam-hari-ini-aku-bangkit")
