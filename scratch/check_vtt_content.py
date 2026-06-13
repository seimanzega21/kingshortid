# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY}

EP_ID = 'c4wbw3q4hvsv0g13683f5ftd'

# 1. Fetch subtitle list from DB
r = requests.get(f"{API_BASE}/episodes/{EP_ID}/subtitles", headers=ADMIN_HDR)
if r.ok:
    subs = r.json()
    print("Subtitles in DB for EP 1 type:", type(subs))
    print("Subtitles in DB for EP 1 value:", subs)
    # Check elements of subs
    if isinstance(subs, list):
        for s in subs:
            if isinstance(s, dict):
                print(f"  ID: {s.get('id')} | Language: {s.get('language')} | URL: {s.get('url')}")
                # Download and check VTT content
                vtt_url = s.get('url')
                if vtt_url:
                    vr = requests.get(vtt_url)
                    print(f"  VTT Status: {vr.status_code}")
                    if vr.ok:
                        print(f"  VTT Content Length: {len(vr.content)}")
                        print(f"  VTT Sample:\n{vr.text[:500]}")
                        print(f"  VTT Tail:\n{vr.text[-300:]}")
            else:
                print(f"  Element of subs is not a dict: {s}")
else:
    print(f"Failed to fetch subtitles. Status: {r.status_code}")

# 2. Fetch upstream unlock info
UPSTREAM_ID = '160000641860'
ep_no = 1
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
}
url = f"https://vidrama.asia/api/idrama2/unlock/{UPSTREAM_ID}/{ep_no}?lang=id"
print(f"\nFetching upstream unlock info from: {url}")
resp = requests.get(url, headers=HEADERS, verify=False, timeout=20)
if resp.ok:
    data = resp.json().get('target_ep_info', {})
    print("Upstream Info:")
    print(f"  Play URL: {data.get('play_url')}")
    all_subs = list(data.get('screentext_list') or []) + list(data.get('subtitle_list') or [])
    for s in all_subs:
        print(f"  Sub Language: {s.get('language')} | URL: {s.get('url')}")
        if s.get('language', '').lower() == 'id':
            sub_url = s.get('url')
            # Fetch upstream subtitle VTT
            sr = requests.get(sub_url, headers=HEADERS, verify=False)
            print(f"    Upstream VTT Status: {sr.status_code}")
            if sr.ok:
                print(f"    Upstream VTT Content Length: {len(sr.content)}")
                print(f"    Upstream VTT Sample:\n{sr.text[:300]}")
else:
    print(f"Failed to fetch upstream unlock info. Status: {resp.status_code}")
