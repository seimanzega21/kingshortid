import json, requests

files = [
    'parsed_satu-insiden-semua-pria-mengi.json',
    'parsed_tak-pernah-terkalahkan-selalu.json',
    'parsed_terbangun-sebagai-suami-terbur.json',
]

for fname in files:
    data = json.load(open(f'd:/kingshortid/scraping/freereels/{fname}', 'r', encoding='utf-8'))
    title = data.get('drama', '?')
    eps = data.get('episodes', [])
    cover = data.get('cover', '')
    print(f"\n{'='*50}")
    print(f"Drama: {title}")
    print(f"Total eps: {len(eps)}")
    print(f"Cover URL: {cover[:80] if cover else 'NONE'}")
    
    # Test first available HLS URL
    for ep in eps:
        h264 = ep.get('h264', '')
        if h264:
            print(f"Sample HLS URL: {h264[:80]}...")
            try:
                r = requests.head(h264, timeout=10, allow_redirects=True)
                print(f"HLS Status: {r.status_code}")
            except Exception as e:
                print(f"HLS Error: {e}")
            break
    else:
        print("WARNING: No HLS URL found in any episode!")
