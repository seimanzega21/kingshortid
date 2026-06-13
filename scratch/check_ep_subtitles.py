# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import warnings
warnings.filterwarnings('ignore')

API_BASE  = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY}

DRAMA_DB_ID = 'izf99mrrimnlsb32gw0pk4n7'

# Get all episodes
r = requests.get(f"{API_BASE}/dramas/{DRAMA_DB_ID}/episodes?includeInactive=true", timeout=15)
eps = r.json()
ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
ep_list.sort(key=lambda x: x.get('episodeNumber', 0))

print(f"Total episodes in DB: {len(ep_list)}\n")
print(f"{'EP':>4} | {'DB ID':28} | {'Has Sub':7} | Subtitle URL")
print("-" * 100)

no_sub = []
for ep in ep_list:
    ep_no  = ep.get('episodeNumber')
    ep_id  = ep.get('id')

    # Fetch subtitles for this episode
    sr = requests.get(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, timeout=10)
    subs = []
    if sr.ok:
        data = sr.json()
        subs = data if isinstance(data, list) else data.get('subtitles', [])

    id_subs = [s for s in subs if s.get('language') == 'id']

    if id_subs:
        sub_url = id_subs[0].get('url', 'N/A')
        print(f"{ep_no:>4} | {ep_id:28} | {'YES':7} | {sub_url[:60]}")
    else:
        print(f"{ep_no:>4} | {ep_id:28} | {'NO':7} | ---")
        no_sub.append({'ep_no': ep_no, 'ep_id': ep_id})

print(f"\n{'='*60}")
print(f"Episodes WITHOUT subtitle: {[x['ep_no'] for x in no_sub]}")
