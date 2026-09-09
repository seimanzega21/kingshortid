import requests

dramas = [
    ("pulau-kiamat-pewaris-darah-purba", "2072916449407352834"),
    ("pangeran-dingin-kini-memanjakanku", "2071481268519649281"),
    ("legenda-sang-raja-perang", "2084571179372765186"),
    ("jatuh-ke-pelukan-ayah-alpha-mantanku", "2090371829822881794"),
    ("ratu-terjatuh-permainan-dimulai", "2090260826665746433")
]

for slug, mid in dramas:
    url = f"https://vidrama.asia/api/dotdrama?action=detail&id={mid}&lang=id"
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    if r.ok:
        data = r.json()
        print(f"[{slug}] Title: {data.get('title')} | Total Eps: {len(data.get('episodes', []))} | Cover: {bool(data.get('cover') or data.get('image'))}")
    else:
        print(f"[{slug}] FAILED status={r.status_code}")
