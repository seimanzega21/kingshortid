import os
import sys
from pprint import pprint

try:
    from prisma import Prisma
except ImportError:
    print("No prisma. Using API instead.")

import requests

API_BASE = 'https://api.shortlovers.id'
DRAMA_ID = 'byv3jp8t6vuqbnyxhfk08qlk'

# Get all episodes
r = requests.get(f'{API_BASE}/api/dramas/{DRAMA_ID}/episodes')
eps = r.json()
if isinstance(eps, dict):
    eps = eps.get('episodes', [])

print(f"Found {len(eps)} episodes")
for ep in eps[:3]:
    ep_id = ep['id']
    ep_num = ep['episodeNumber']
    r2 = requests.get(f'{API_BASE}/api/episodes/{ep_id}/subtitles')
    subs = r2.json()
    print(f"EP {ep_num} ({ep_id}): {subs}")
