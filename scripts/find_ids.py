import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

titles_to_find = [
    "Krisis Mineral Penuh Intrik",
    "Permainan Hasrat Khusus Sang CEO",
    "Menantu Kerajaan dari Masa Depan",
    "Demi Putriku, Identitasku Bocor"
]

found = {}
for page in range(1, 10):
    print(f"Checking page {page}...")
    url = f"{VIDRAMA_API}/feed/{page}?lang=id_ID"
    r = requests.get(url, headers=WEB_HDRS, verify=False)
    items = r.json().get('data', [])
    for it in items:
        title = it.get('title', '')
        for t in titles_to_find:
            if t.lower() in title.lower():
                found[t] = {'title': title, 'id': it.get('id')}
                print(f"FOUND: {title} -> {it.get('id')}")

print("\nRESULTS:")
for t, data in found.items():
    print(f"{{'title': '{data['title']}', 'drama_id': '{data['id']}', 'slug': ''}},")
