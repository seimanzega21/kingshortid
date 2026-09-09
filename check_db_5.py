import requests

titles = [
    "Pulau Kiamat: Pewaris Darah Purba",
    "Pangeran Dingin Kini Memanjakanku",
    "Legenda Sang Raja Perang",
    "Jatuh ke Pelukan Ayah Alpha Mantanku",
    "Ratu Terjatuh, Permainan Dimulai"
]

r = requests.get('http://141.11.160.187:3000/api/dramas?limit=5000', timeout=15)
if r.ok:
    dramas = r.json() if isinstance(r.json(), list) else r.json().get('dramas', [])
    existing_titles = {d.get('title', '').strip().lower(): d for d in dramas}
    for t in titles:
        match = existing_titles.get(t.lower())
        if match:
            print(f"ALREADY IN DB: {t} -> ID: {match['id']}")
        else:
            print(f"NOT IN DB: {t}")
