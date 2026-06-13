import requests
import urllib3
import json

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

# The target drama ID is 161004641891
movie_id = '161004641891'

endpoints = [
    # netshortv2 endpoint patterns
    (f"https://vidrama.asia/api/netshortv2/movie/{movie_id}?provider=idrama2&lang=id_ID", "netshortv2_movie_provider_idrama2"),
    (f"https://vidrama.asia/api/netshortv2/movie/{movie_id}?provider=idrama&lang=id_ID", "netshortv2_movie_provider_idrama"),
    (f"https://vidrama.asia/api/netshortv2/detail/{movie_id}?provider=idrama2&lang=id_ID", "netshortv2_detail_provider_idrama2"),
    (f"https://vidrama.asia/api/netshortv2/detail/{movie_id}?lang=id_ID", "netshortv2_detail_no_provider"),
    
    # dramabox3 watch patterns
    (f"https://vidrama.asia/api/dramabox3/watch?bookId={movie_id}&episode=1&lang=id", "dramabox3_watch_lang_id"),
    (f"https://vidrama.asia/api/dramabox3/detail?bookId={movie_id}&lang=id", "dramabox3_detail_lang_id"),
    
    # Generic nextjs api patterns if any
    (f"https://vidrama.asia/api/movie/{movie_id}?provider=idrama2&lang=id_ID", "api_movie_idrama2"),
    (f"https://vidrama.asia/api/movie/detail/{movie_id}?provider=idrama2&lang=id_ID", "api_movie_detail_idrama2"),
    
    # Episode level stream patterns on netshortv2
    (f"https://vidrama.asia/api/netshortv2/episode/{movie_id}/1?provider=idrama2&lang=id_ID", "netshortv2_ep_idrama2"),
    (f"https://vidrama.asia/api/netshortv2/episode/{movie_id}?provider=idrama2&lang=id_ID", "netshortv2_ep_idrama2_no_num"),
]

for url, label in endpoints:
    print(f"Testing {label}: {url}...")
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"  --> Status: {r.status_code}")
        if r.ok:
            try:
                data = r.json()
                print(f"      Success: {data.get('code') or data.get('success') or data.get('msg')}")
                if 'data' in data:
                    d = data.get('data')
                    if isinstance(d, dict):
                        print(f"      Keys: {list(d.keys())}")
                        if 'episodes' in d:
                            print(f"      Episodes count: {len(d['episodes'])}")
                    else:
                        print(f"      Data: {str(d)[:150]}")
            except:
                print(f"      Response (text first 150): {r.text[:150]}")
        else:
            print(f"      Response (text first 150): {r.text[:150]}")
    except Exception as e:
        print(f"      Exception: {e}")
