import requests
import json
import urllib3
import sys

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

video_id = "1ZkXla"
episodes_url = f"https://vidrama.asia/api/proxy-cubetv/episodes/{video_id}?lang=id"

r = requests.get(episodes_url, headers=WEB_HDRS, verify=False, timeout=15)
if r.ok:
    data = r.json()
    eps = data if isinstance(data, list) else data.get('rows', data.get('data', []))
    print(f"Total episodes: {len(eps)}")
    for ep in eps:
        ep_no = ep.get('episodeNumber')
        ep_id = ep.get('episodeid')
        charge = ep.get('chargeCoin')
        lock = ep.get('lockStatus')
        video_urls = ep.get('videoUrls', [])
        subs = ep.get('subtitles', [])
        
        has_video = len(video_urls) > 0
        has_sub = any(s.get('lang') == 'id' for s in subs)
        
        print(f"Ep {ep_no} (ID: {ep_id}): Coin={charge}, Lock={lock}, HasVideo={has_video}, HasIndoSub={has_sub}")
        if has_video:
            print(f"  - Stream URL: {video_urls[0]['url'][:80]}...")
else:
    print("Failed to get episodes:", r.status_code)
