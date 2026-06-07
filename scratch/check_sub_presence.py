# -*- coding: utf-8 -*-
import requests
import json

api_base = 'https://api.shortlovers.id/api'
admin_key = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
headers = {'x-admin-key': admin_key, 'Content-Type': 'application/json'}

drama_id = 'p1ltussvszgvc1x3wxm5ouuk'

r_eps = requests.get(f"{api_base}/dramas/{drama_id}/episodes", headers=headers)
if r_eps.ok:
    eps = r_eps.json()
    for ep in eps:
        ep_id = ep.get('id')
        print(f"Episode {ep.get('episodeNumber')} (ID: {ep_id}):")
        # Try GET /episodes/{ep_id}/subtitles
        r_sub = requests.get(f"{api_base}/episodes/{ep_id}/subtitles", headers=headers)
        print(f"  GET /episodes/{ep_id}/subtitles -> Status: {r_sub.status_code}")
        if r_sub.ok:
            print("  Body:", json.dumps(r_sub.json(), indent=2))
        else:
            print("  Body:", r_sub.text)
else:
    print("Error:", r_eps.text)
