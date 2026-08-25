import requests
h = {'x-admin-key': '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'}
drama_id = 'o50l6hc0viuk5m50ezhjge2c'
episodes = requests.get(f'http://141.11.160.187:3000/api/dramas/{drama_id}/episodes', timeout=10).json()

for ep in episodes:
    ep_no = ep['episodeNumber']
    url_720 = ep.get('videoUrl', '').split('?')[0] + '?v=2'
    url_540 = ep.get('videoUrl540p', '').split('?')[0] + '?v=2' if ep.get('videoUrl540p') else ''
    
    requests.put(
        f'http://141.11.160.187:3000/api/admin/dramas/{drama_id}/episodes/{ep_no}',
        headers=h,
        json={'videoUrl': url_720, 'videoUrl540p': url_540}
    )
print('Done updating DB to bypass cache!')
