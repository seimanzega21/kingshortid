import requests, json

dramas = json.load(open('vidrama_all_dramas.json','r',encoding='utf-8'))
d = [x for x in dramas if x['title']=='Mafia yang Kucintai'][0]

print("=== CACHED DATA ===")
print("Keys:", list(d.keys()))
print("Image:", (d.get('image') or 'NONE')[:200])
print("Poster:", (d.get('poster') or 'NONE')[:200])
print("OrigImg:", (d.get('originalImage') or 'NONE')[:200])
print("Desc:", (d.get('description') or d.get('synopsis') or 'NONE')[:200])

# Detail API
r = requests.get('https://vidrama.asia/api/melolo?action=detail&id=' + d['id'], timeout=30)
detail = r.json().get('data', {})
print("\n=== DETAIL API ===")
print("Keys:", list(detail.keys()))
print("Description:", (detail.get('description') or detail.get('synopsis') or 'NONE')[:200])
print("Image:", (detail.get('image') or detail.get('poster') or detail.get('cover') or 'NONE')[:200])

# Test download cover
cover_url = d.get('image') or d.get('poster') or ''
if cover_url:
    print("\n=== COVER DOWNLOAD TEST ===")
    print("URL:", cover_url[:120])
    try:
        cr = requests.get(cover_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        print("Status:", cr.status_code)
        print("Content-Type:", cr.headers.get('Content-Type', '?'))
        print("Content-Length:", len(cr.content))
    except Exception as e:
        print("Error:", e)
