# -*- coding: utf-8 -*-
import requests, json, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

drama_id = '7653295748544465973'
lang = 'id'

# Test 1: Series detail
url_detail = f'https://vidrama.asia/api/melolov3/series?id={drama_id}&lang={lang}'
print("Querying detail:", url_detail)
try:
    r = requests.get(url_detail, headers=WEB_HDRS, timeout=15, verify=False)
    print("Status:", r.status_code)
    if r.ok:
        data = r.json()
        print("Detail Keys:", list(data.keys()))
        if 'series' in data:
            print("  Title:", data['series'].get('title'))
            print("  Intro:", data['series'].get('intro'))
            print("  Cover:", data['series'].get('cover'))
            print("  Episodes Count:", data['series'].get('episode_count'))
except Exception as e:
    print("Detail Error:", e)

print("-" * 60)

# Test 2: Multi video list
url_videos = f'https://vidrama.asia/api/melolov3/multi-video?id={drama_id}&lang={lang}'
print("Querying videos:", url_videos)
try:
    r = requests.get(url_videos, headers=WEB_HDRS, timeout=15, verify=False)
    print("Status:", r.status_code)
    if r.ok:
        data = r.json()
        print("Videos keys/type:", type(data).__name__)
        if isinstance(data, dict):
            print("  Keys:", list(data.keys()))
            eps = data.get('episodes', [])
            print("  Episodes Count:", len(eps))
            if eps:
                print("  First Episode Index:", eps[0].get('index'))
                print("  First Episode Title:", eps[0].get('title'))
                print("  First Episode URL:", eps[0].get('stream_url'))
        elif isinstance(data, list):
            print("  List Length:", len(data))
            if data:
                print("  First Episode Index:", data[0].get('index'))
                print("  First Episode Title:", data[0].get('title'))
                print("  First Episode URL:", data[0].get('stream_url'))
except Exception as e:
    print("Videos Error:", e)
