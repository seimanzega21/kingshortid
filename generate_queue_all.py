import json
import re

text = """
1. https://vidrama.asia/movie/kotak-antar-ke-masa-lalu--7668524686103317509?provider=melolov3&lang=id
2. https://vidrama.asia/movie/balas-budi-penyelamatku--7665963996851211269?provider=melolov3&lang=id
3. https://vidrama.asia/movie/kaya-raya-kembali-ke-sma--7666274601487322165?provider=melolov3&lang=id
4. https://vidrama.asia/movie/kaya-sebelum-lulus-kuliah-2--7668524685918751797?provider=melolov3&lang=id
5. https://vidrama.asia/movie/rahasia-anak-sultan--7619622710204713989?provider=melolov3&lang=id
6. https://vidrama.asia/movie/kekayaan-mendadak--7665940057064393781?provider=melolov3&lang=id
7. https://vidrama.asia/movie/juragan-hasil-laut--7679397478600281141?provider=melolov3&lang=id
8. https://vidrama.asia/movie/lord-koin-emas-harian--7669998858033712181?provider=melolov3&lang=id
9. https://vidrama.asia/movie/beban-hidup-sang-kuli--7673350378645113909?provider=melolov3&lang=id
10. https://vidrama.asia/movie/dokter-ajaib-dari-desa--7679395787037477941?provider=melolov3&lang=id
11. https://vidrama.asia/movie/kembalinya-sang-koki--7632578881286851589?provider=melolov3&lang=id
12. https://vidrama.asia/movie/bangkit-sama-kak-putri--7678225964827937845?provider=melolov3&lang=id
13. https://vidrama.asia/movie/hidup-lagi-tak-perlu-cinta--7671948251137838133?provider=melolov3&lang=id
14. https://vidrama.asia/movie/menaklukkan-liga-eropa-1--7670431405926517813?provider=melolov3&lang=id
15. https://vidrama.asia/movie/pemuda-miskin-jadi-bos-kaya--7672696931004451893?provider=melolov3&lang=id
16. https://vidrama.asia/movie/ruang-mata-air-spiritual--7677209787829849141?provider=melolov3&lang=id
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
