# -*- coding: utf-8 -*-
import requests
import json

api_base = 'https://api.shortlovers.id/api'
admin_key = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
headers = {'x-admin-key': admin_key, 'Content-Type': 'application/json'}

drama_id = 'p1ltussvszgvc1x3wxm5ouuk'

print(f"--- Verifying Drama in DB: {drama_id} ---")
r = requests.get(f"{api_base}/dramas/{drama_id}", headers=headers)
print("Drama Status Code:", r.status_code)
if r.ok:
    print(json.dumps(r.json(), indent=2))
else:
    print(r.text)

print(f"\n--- Verifying Episodes for Drama: {drama_id} ---")
r_eps = requests.get(f"{api_base}/dramas/{drama_id}/episodes", headers=headers)
print("Episodes Status Code:", r_eps.status_code)
if r_eps.ok:
    eps = r_eps.json()
    print(f"Total episodes found in DB: {len(eps)}")
    for ep in eps:
        print(f"Episode {ep.get('episodeNumber')}:")
        print(f"  Title: {ep.get('title')}")
        print(f"  720p: {ep.get('videoUrl')}")
        print(f"  540p: {ep.get('videoUrl540p')}")
        
        # Subtitles
        subtitles = ep.get('subtitles', [])
        print(f"  Subtitles count: {len(subtitles)}")
        for s in subtitles:
            print(f"    Sub: language={s.get('language')}, url={s.get('url')}, default={s.get('isDefault')}")
else:
    print(r_eps.text)
