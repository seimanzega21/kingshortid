"""
Explore episodes that are embedded in the detail response.
"""
import requests
import json

HEADERS = {'User-Agent': 'Mozilla/5.0'}
DRAMA_ID = "2036690458087784450"

r = requests.get(f"https://vidrama.asia/api/netshortv2/detail/{DRAMA_ID}?lang=id_ID", headers=HEADERS)
data = r.json().get('data', {})
episodes = data.get('episodes', [])
print(f"Total episodes in detail: {len(episodes)}")
if episodes:
    ep = episodes[0]
    print("Episode 1 keys:", list(ep.keys()))
    print("Episode 1:", json.dumps(ep, ensure_ascii=False, indent=2)[:800])

    # Last episode
    ep_last = episodes[-1]
    print(f"\nEpisode {len(episodes)} keys:", list(ep_last.keys()))
    print("Episode last:", json.dumps(ep_last, ensure_ascii=False, indent=2)[:800])
