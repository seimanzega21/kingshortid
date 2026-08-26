import json
import re

text = """
1. https://vidrama.asia/movie/dewa-petir-sss-tersembunyi--2089169768653586433?provider=netshortv2&lang=id_ID
2. https://vidrama.asia/movie/rahasia-di-kursi-belakang--2080576395143299074?provider=netshortv2&lang=id_ID
3. https://vidrama.asia/movie/hasrat-terlarang-yang-tak-terkendali--2082649007530532865?provider=netshortv2&lang=id_ID
4. https://vidrama.asia/movie/jiwa-iblis-dibalik-zirah-berat--2088091241606656002?provider=netshortv2&lang=id_ID
5. https://vidrama.asia/movie/jalan-kebangkitan-gadis-gemuk--2086724984822722561?provider=netshortv2&lang=id_ID
6. https://vidrama.asia/movie/saat-cinta-habis-hukum-suami-brengsek--2088785660060430338?provider=netshortv2&lang=id_ID
7. https://vidrama.asia/movie/ksatria-bertangan-satu--2088790562107092993?provider=netshortv2&lang=id_ID
8. https://vidrama.asia/movie/jalan-keinginan-terlarang--2088795410701549569?provider=netshortv2&lang=id_ID
9. https://vidrama.asia/movie/ksatria-pemabuk-kembali-berjaya--2088794595647619074?provider=netshortv2&lang=id_ID
10. https://vidrama.asia/movie/kekuasaan-raja-di-balik-setir--2089655770371903489?provider=netshortv2&lang=id_ID
11. https://vidrama.asia/movie/penyesalan-mantan-miliarder--2080494372252827650?provider=netshortv2&lang=id_ID
12. https://vidrama.asia/movie/balas-dendam-atas-nama-kakak--2069274865185570818?provider=netshortv2&lang=id_ID
13. https://vidrama.asia/movie/kekuasaan-tak-pernah-diam--2085542957637001217?provider=netshortv2&lang=id_ID
14. https://vidrama.asia/movie/aroma-yang-hanya-miliknya--2076587230309847041?provider=netshortv2&lang=id_ID
15. https://vidrama.asia/movie/kuasai-dunia-dengan-mata-batin--2019647541203910657?provider=netshortv2&lang=id_ID
"""

dramas = []
for line in text.strip().split('\n'):
    match = re.search(r'/movie/([^?]+)\-\-(\d+)', line)
    if match:
        slug = match.group(1)
        did = match.group(2)
        dramas.append({"slug": slug, "id": did, "lang": "id_ID"})

with open('new_netshort_dramas.json', 'w') as f:
    json.dump(dramas, f, indent=2)

print(f"Created json with {len(dramas)} dramas")
