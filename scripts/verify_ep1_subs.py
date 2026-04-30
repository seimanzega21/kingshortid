import requests

ADMIN_KEY='00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
drama_id='dd0ztunafaosotezggkdqp0g'

res = requests.get(f'https://api.shortlovers.id/api/dramas/{drama_id}?includeInactive=true', 
                   headers={'x-admin-key': ADMIN_KEY}).json()

ep1 = next(e for e in res['episodes'] if e['episodeNumber'] == 1)
print(f"Episode 1 ID: {ep1['id']}")

subs = requests.get(f"https://api.shortlovers.id/api/episodes/{ep1['id']}/subtitles", 
                    headers={'x-admin-key': ADMIN_KEY}).json()
print(subs)
