import requests
import json

headers = {'x-admin-key': '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'}
r = requests.get('http://141.11.160.187:3002/api/admin/dramas?limit=5000', headers=headers, timeout=20)
dramas = r.json().get('dramas', [])
d = next((x for x in dramas if 'Kekuatan Uang' in x['title']), None)

if d:
    print('Found ID:', d['id'])
    payload = {
        'description': 'Logan, miliarder menyamar sebagai petugas kebersihan demi cinta, tapi malah diputus pacar matre. Tak disangka, ia menikah dengan CEO Eleanor. Mereka menghadapi cemoohan, mengungkap jati diri, kalahkan musuh, dan menunjukkan kekuatan Logan, akhirnya naik ke puncak.'
    }
    headers = {'x-admin-key': '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'}
    resp = requests.put(f'http://141.11.160.187:3002/api/admin/dramas/{d["id"]}', json=payload, headers=headers)
    print(resp.status_code, resp.text)
else:
    print('Not found')
