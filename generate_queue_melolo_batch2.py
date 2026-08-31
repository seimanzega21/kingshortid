import json
import re

text = """
17. https://vidrama.asia/movie/dewa-pedang-legendaris--7518935469413895184?provider=melolov3&lang=id
18. https://vidrama.asia/movie/putra-dewa-kegelapan--7630751381267156021?provider=melolov3&lang=id
19. https://vidrama.asia/movie/ular-pemangsa-dunia--7656363850924559413?provider=melolov3&lang=id
20. https://vidrama.asia/movie/kembalinya-permaisuri--7597619763061197877?provider=melolov3&lang=id
21. https://vidrama.asia/movie/keajaiban-kolam-andi--7660746804895419445?provider=melolov3&lang=id
22. https://vidrama.asia/movie/kisah-dokter-sakti-andika--7658188265446444037?provider=melolov3&lang=id
23. https://vidrama.asia/movie/dipecat-jadi-bos-bengkel--7665183873151585285?provider=melolov3&lang=id
24. https://vidrama.asia/movie/sentuhan-ajaib-sang-mekanik--7598484306838703109?provider=melolov3&lang=id
25. https://vidrama.asia/movie/raja-daging-rebus--7649951469453446197?provider=melolov3&lang=id
26. https://vidrama.asia/movie/dari-turis-jadi-bos-pasar-gelap--7627152274543873077?provider=melolov3&lang=id
27. https://vidrama.asia/movie/antar-makanan-dapat-bidadari--7639705987405859845?provider=melolov3&lang=id
28. https://vidrama.asia/movie/tahun-1983-dimulai-dari-bengkel--7600000235787521077?provider=melolov3&lang=id
29. https://vidrama.asia/movie/sampah-jadi-emas--7669997668374072373?provider=melolov3&lang=id
30. https://vidrama.asia/movie/mata-naga-penguasa-harta--7620403857952082949?provider=melolov3&lang=id
31. https://vidrama.asia/movie/berkah-sepasang-mata-emas--7662952819380456501?provider=melolov3&lang=id
32. https://vidrama.asia/movie/mata-ajaib-sari--7636714569318009861?provider=melolov3&lang=id
"""

dramas = []
for line in text.strip().split('\n'):
    match = re.search(r'/movie/([^?]+)\-\-(\d+)', line)
    if match:
        slug = match.group(1)
        did = match.group(2)
        dramas.append({"slug": slug, "id": did, "lang": "id", "genres": ["Drama"]})

with open('new_melolov3_dramas.json', 'w') as f:
    json.dump(dramas, f, indent=2)

print(f"Created json with {len(dramas)} dramas")
