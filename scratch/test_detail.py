import requests
import urllib3
urllib3.disable_warnings()

vid_id = 'TxCz3hQFxJ'
endpoints = [
    f'https://vidrama.asia/api/freereels/detail?id={vid_id}',
    f'https://vidrama.asia/api/freereel/detail?id={vid_id}',
    f'https://vidrama.asia/api/provider/detail?id={vid_id}',
    f'https://vidrama.asia/api/detail?id={vid_id}',
    f'https://vidrama.asia/api/dramabox/detail?id={vid_id}'
]

for url in endpoints:
    r = requests.get(url, verify=False)
    print(f"{url} -> {r.status_code}")
    if r.ok:
        print(r.text[:200])
