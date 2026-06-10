import requests
import urllib3
urllib3.disable_warnings()

vid_id = 'TxCz3hQFxJ'
endpoints = [
    f'https://vidrama.asia/api/freereels?action=detail&id={vid_id}',
    f'https://vidrama.asia/api/freereels?action=info&id={vid_id}',
    f'https://vidrama.asia/api/freereels?id={vid_id}',
    f'https://vidrama.asia/api/freereels?action=video&id={vid_id}&episode=1'
]

for url in endpoints:
    r = requests.get(url, verify=False)
    print(f"{url} -> {r.status_code}")
    if r.ok:
        print(r.text[:200])
