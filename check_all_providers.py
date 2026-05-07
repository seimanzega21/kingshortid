import requests, json, urllib3
urllib3.disable_warnings()

PROVIDERS = [
    'netshortv2', 'netshort', 'melolov2', 'dramawavev2', 'dramanova', 
    'starshort', 'radreels', 'shotshort', 'happyshort', 'cubetv'
]
ID = '1894650560457961473'
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

def check_providers():
    found_ep32 = []
    for p in PROVIDERS:
        url = f"https://vidrama.asia/api/netshortv2/movie/{ID}?provider={p}&lang=id_ID"
        print(f"Checking provider: {p}...")
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=10, verify=False)
            if r.ok:
                data = r.json()
                episodes = data.get('data', {}).get('episodes', [])
                ep32 = next((ep for ep in episodes if ep.get('order') == 32), None)
                if ep32:
                    is_vip = ep32.get('is_vip', False)
                    print(f"  [+] Episode 32 found! VIP: {is_vip}")
                    if not is_vip:
                        # Try to get stream URL
                        video_id = ep32.get('id')
                        stream_url = f"https://vidrama.asia/api/netshortv2/episode/{video_id}?lang=id_ID"
                        sr = requests.get(stream_url, headers=WEB_HDRS, timeout=10, verify=False)
                        if sr.ok:
                            sdata = sr.json()
                            url_video = sdata.get('data', {}).get('video_url')
                            if url_video:
                                print(f"  [!] Stream URL: {url_video}")
                                found_ep32.append({
                                    'provider': p,
                                    'url': url_video
                                })
            else:
                print(f"  [-] Error {r.status_code}")
        except Exception as e:
            print(f"  [X] Error: {e}")
    
    return found_ep32

if __name__ == "__main__":
    results = check_providers()
    if results:
        with open('found_urls.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("\nSuccess!")
    else:
        print("\nNo free stream found for episode 32.")
