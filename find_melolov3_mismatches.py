import requests
API_BASE = 'http://141.11.160.187:3000'
r = requests.get(f'{API_BASE}/api/dramas?limit=5000', timeout=60)
data = r.json()
dramas = data if isinstance(data, list) else data.get('dramas', [])

searches = {
    'ruang-mata-air-spiritual': ['ruang', 'mata', 'air'],
    'putra-dewa-kegelapan': ['putra', 'kegelapan'],
    'ular-pemangsa-dunia': ['ular', 'pemangsa'],
    'kembalinya-permaisuri': ['permaisuri'],
    'kisah-dokter-sakti-andika': ['dokter', 'andika'],
    'dipecat-jadi-bos-bengkel': ['dipecat', 'bengkel'],
    'sentuhan-ajaib-sang-mekanik': ['sentuhan', 'mekanik'],
    'dari-turis-jadi-bos-pasar-gelap': ['turis', 'pasar'],
    'antar-makanan-dapat-bidadari': ['makanan', 'bidadari'],
    'tahun-1983-dimulai-dari-bengkel': ['1983'],
    'berkah-sepasang-mata-emas': ['berkah', 'emas'],
    'mata-ajaib-sari': ['ajaib', 'sari'],
}

for slug, words in searches.items():
    hits = [d for d in dramas if all(w in d.get('title','').lower() for w in words)]
    if hits:
        for h in hits:
            did = h['id']
            ep_r = requests.get(f'{API_BASE}/api/dramas/{did}/episodes', timeout=10)
            ep_count = len(ep_r.json()) if ep_r.ok else '?'
            status = 'OK' if ep_count == h.get('totalEpisodes') else 'INCOMPLETE'
            print(f"[{status}] {slug}")
            print(f"       -> {h['title']} | total:{h.get('totalEpisodes')} | actual:{ep_count}")
    else:
        print(f"[NOT FOUND] {slug}")
