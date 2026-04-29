"""
Find stream URL for an episode using its episodeId.
"""
import requests
import json

HEADERS = {'User-Agent': 'Mozilla/5.0'}
EPISODE_ID = "2044716745389768710"  # Episode 1 of Pemilik Kitab Pedang
DRAMA_ID = "2036690458087784450"

for endpoint in [
    f"https://vidrama.asia/api/netshortv2/stream/{EPISODE_ID}?lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/video/{EPISODE_ID}?lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/play/{EPISODE_ID}?lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/episode/{EPISODE_ID}?lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/episode?episodeId={EPISODE_ID}&lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/stream?id={DRAMA_ID}&episodeId={EPISODE_ID}&lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/stream?episodeId={EPISODE_ID}&lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/play?id={DRAMA_ID}&ep=1&lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/play?episodeId={EPISODE_ID}&lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/episode/{EPISODE_ID}/stream?lang=id_ID",
]:
    try:
        r = requests.get(endpoint, headers=HEADERS, timeout=8)
        print(f"URL: {endpoint}")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            print(f"Data: {json.dumps(d, ensure_ascii=False)[:600]}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()
