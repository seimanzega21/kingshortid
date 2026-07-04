import requests
import json
import urllib3
import sys

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

movie_id = '2pOLP7uNmB'
url = f"https://vidrama.asia/api/dramawave?action=detail&id={movie_id}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

r = requests.get(url, headers=headers, verify=False, timeout=15)
print("Status Code:", r.status_code)
if r.ok:
    data = r.json()
    print("Success:", data.get('success'))
    meta = data.get('data', {})
    print("Title:", meta.get('title') or meta.get('bookName'))
    print("Description:", meta.get('description'))
    print("Cover:", meta.get('cover'))
    episodes = meta.get('list', [])
    print("Total Episodes in List:", len(episodes))
    if episodes:
        first_ep = episodes[0]
        print("\nFirst Episode Info:")
        print("  Episode No:", first_ep.get('episodeNo'))
        print("  Video Path (prefix):", first_ep.get('videoPath')[:80] if first_ep.get('videoPath') else 'None')
        subs = first_ep.get('subtitles', [])
        print("  Subtitles count:", len(subs))
        for s in subs:
            if s.get('language') in ['id-ID', 'id', 'in', 'in-ID', 'id_ID', 'en-US', 'en']:
                print(f"    Sub lang: {s.get('language')} | Display: {s.get('display_name')} | URL: {s.get('subtitle') or s.get('vtt')}")
else:
    print(r.text)
