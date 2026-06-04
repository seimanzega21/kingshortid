import requests

API_BASE = 'https://api.shortlovers.id/api'
DRAMA_ID = 'o8wdjeeh9y5iq7puuq8c689h'

r = requests.get(f"{API_BASE}/dramas/{DRAMA_ID}/episodes?includeInactive=true")
if r.ok:
    eps = r.json()
    ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
    print(f"Total episodes: {len(ep_list)}")
    
    no_subs = []
    has_subs = []
    
    for ep in sorted(ep_list, key=lambda x: x.get('episodeNumber', 0)):
        ep_no = ep.get('episodeNumber')
        ep_id = ep.get('id')
        
        sub_r = requests.get(f"{API_BASE}/episodes/{ep_id}/subtitles")
        if sub_r.ok:
            subs = sub_r.json()
            sub_list = subs if isinstance(subs, list) else subs.get('subtitles', subs.get('data', []))
            if not sub_list:
                no_subs.append(ep_no)
            else:
                has_subs.append((ep_no, [s.get('language') for s in sub_list]))
        else:
            print(f"Failed to query EP {ep_no}")
            
    print(f"Episodes WITH subtitles ({len(has_subs)}):", has_subs)
    print(f"Episodes WITHOUT subtitles ({len(no_subs)}):", no_subs)
else:
    print("Failed to query episodes")
