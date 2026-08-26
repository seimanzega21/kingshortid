import requests
import json
import urllib3
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://vidrama.asia/'
}

drama_id = "2089169768653586433"
provider = "netshortv2"

endpoints = [
    f"https://vidrama.asia/api/{provider}",
    f"https://vidrama.asia/api/proxy-{provider}",
    f"https://vidrama.asia/api/proxy-netshort",
]
actions = ['detail', 'chapters', 'episode', 'info', 'stream', 'play', 'movie']

for base in endpoints:
    for action in actions:
        url = f"{base}?action={action}&playletId={drama_id}&id={drama_id}&lang=id_ID"
        try:
            r = requests.get(url, headers=headers, timeout=5, verify=False)
            if r.status_code != 404:
                print(f"[{r.status_code}] {url}")
                try:
                    print("  ", r.text[:200])
                except:
                    pass
        except Exception as e:
            pass
