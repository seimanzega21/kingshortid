import requests, json, urllib3
urllib3.disable_warnings()

ID = '1894650560457961473'
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

def get_microdrama_detail():
    url = f"https://vidrama.asia/api/microdrama?action=detail&id={ID}"
    print(f"Fetching: {url}")
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            episodes = data.get('episodes', [])
            print(f"Found {len(episodes)} episodes")
            ep32 = next((ep for ep in episodes if ep.get('index') == 32), None)
            if ep32:
                print("Episode 32 found!")
                print(json.dumps(ep32, indent=2))
            else:
                print("Episode 32 not found in microdrama detail")
        else:
            print(r.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_microdrama_detail()
