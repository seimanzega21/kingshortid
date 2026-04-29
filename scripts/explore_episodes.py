"""
Explore Netshort V2 episode and stream API.
"""
import requests
import json

HEADERS = {'User-Agent': 'Mozilla/5.0'}
DRAMA_ID = "2036690458087784450"  # Pemilik Kitab Pedang

# Check full detail
r = requests.get(f"https://vidrama.asia/api/netshortv2/detail/{DRAMA_ID}?lang=id_ID", headers=HEADERS)
data = r.json()
detail = data.get('data', {})
print("Detail keys:", list(detail.keys()))
print("totalEpisodes:", detail.get('totalEpisodes'))

# Try episode list endpoint
for ep_endpoint in [
    f"https://vidrama.asia/api/netshortv2/episodes/{DRAMA_ID}?lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/detail/{DRAMA_ID}/episodes?lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/{DRAMA_ID}/episodes?lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/episode?id={DRAMA_ID}&ep=1&lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/play/{DRAMA_ID}?ep=1&lang=id_ID",
]:
    try:
        r = requests.get(ep_endpoint, headers=HEADERS, timeout=8)
        print(f"\n  URL: {ep_endpoint}")
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            print(f"  Data: {json.dumps(d, ensure_ascii=False)[:500]}")
    except Exception as e:
        pass
