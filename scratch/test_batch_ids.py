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

drama_ids = ["m0WBLa", "QZpz60"]

for video_id in drama_ids:
    print(f"\n==================== PROBING ID: {video_id} ====================")
    detail_url = f"https://vidrama.asia/api/proxy-cubetv/detail/{video_id}?lang=id"
    episodes_url = f"https://vidrama.asia/api/proxy-cubetv/episodes/{video_id}?lang=id"
    
    # Detail
    r_det = requests.get(detail_url, headers=WEB_HDRS, verify=False, timeout=15)
    if r_det.ok:
        det = r_det.json().get('data', {})
        print("Title:", det.get('videoName'))
        print("Total Episodes in Detail:", det.get('totalEpisodeNum'))
        print("Cover:", det.get('cover'))
        print("TagInfo:", det.get('tagInfo'))
    else:
        print("Failed detail:", r_det.status_code)
        continue
        
    # Episodes
    r_eps = requests.get(episodes_url, headers=WEB_HDRS, verify=False, timeout=15)
    if r_eps.ok:
        eps = r_eps.json()
        eps_list = eps if isinstance(eps, list) else eps.get('rows', eps.get('data', []))
        print("Total Episodes in List:", len(eps_list))
        if eps_list:
            first_ep = eps_list[0]
            print("First Ep Num:", first_ep.get('episodeNumber'))
            video_urls = first_ep.get('videoUrls', [])
            subs = first_ep.get('subtitles', [])
            print(f"First Ep Has Video: {len(video_urls) > 0}, Has Subtitles: {len(subs) > 0}")
            if video_urls:
                print("First Ep Stream URL Prefix:", video_urls[0]['url'][:80])
            print("Subtitle languages available:", [s.get('lang') for s in subs])
    else:
        print("Failed episodes:", r_eps.status_code)
