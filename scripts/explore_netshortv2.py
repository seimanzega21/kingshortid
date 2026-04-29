"""
Explore Netshort V2 API to get drama details and episode video URLs.
"""
import requests
import json

HEADERS = {'User-Agent': 'Mozilla/5.0'}

DRAMA_IDS = {
    "pemilik-kitab-pedang": "2036690458087784450",
    "jenderal-masakanku-siap": "2045396177699995650",
    "kode-cinta-robot": "2044326309693227010",
    "dia-kembali-dari-balik-legenda": "2011980833696841730",
}

for slug, drama_id in DRAMA_IDS.items():
    print(f"\n{'='*60}")
    print(f"Slug: {slug}")
    print(f"ID: {drama_id}")
    
    # Try detail endpoints
    for endpoint in [
        f"https://vidrama.asia/api/netshortv2/detail/{drama_id}?lang=id_ID",
        f"https://vidrama.asia/api/microdrama?action=detail&id={slug}--{drama_id}",
        f"https://vidrama.asia/api/microdrama?action=detail&id={drama_id}",
        f"https://vidrama.asia/api/netshortv2/episodes/{drama_id}?lang=id_ID",
    ]:
        try:
            r = requests.get(endpoint, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json()
                print(f"\n  URL: {endpoint}")
                print(f"  Keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                print(f"  Snippet: {json.dumps(data, ensure_ascii=False)[:400]}")
        except Exception as e:
            pass
