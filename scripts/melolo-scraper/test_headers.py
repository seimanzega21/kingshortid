import requests

headers = {
    'accept': 'text/x-component',
    'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'text/plain;charset=UTF-8',
    'next-action': '608cb6ff9c19dd8c5454a1f2782fc7baa0e774a348',
    'next-router-state-tree': '%5B%22%22%2C%7B%22children%22%3A%5B%22(main)%22%2C%7B%22children%22%3A%5B%22watch%22%2C%7B%22children%22%3A%5B%22%5Bslug%5D%22%2C%7B%22children%22%3A%5B%22%5Beps%5D%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%5D%7D%5D%7D%5D%7D%5D%7D%5D%7D%5D',
    'origin': 'https://vidrama.asia',
    'referer': 'https://vidrama.asia/watch/dubbingsopir-taksi-mantan-dewa-balap--846959/1?provider=shortmax',
    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36',
    'cookie': 'sb-gkcnbnlfqdlotnjaizxx-auth-token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdrY25ibmxmcWRsb3RuamFpenh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg0NjQ5ODEsImV4cCI6MjA4NDA0MDk4MX0.EFP6qcUAT_Dk0bV3ycjxpduZ1MBuhCWOTE0ArIsS9Xo; cf_clearance=da_XzER9EpsQhMtP9b.sVZGNd7aLyClwY_F9bCUpRJ0-1777189787-1.2.1.1-GEkPqyfpXxAyNLTe5TTrTdSAFrTO4a4ZBWTnFvlahImB4zpo.dJKEuIrQq4tZGEqCVPMdgSOKQQSsUAOfyr1F4.s7DsCxZWedMKyn2vlm0E6DOzips9vCzxDp7XkmBf9KT2bLVwwMCSx3Mm3RzrGCKQPggbN8d7Ql3Agfo_yanbv.5fZvEnXLeqaCPzalFyNAQIHIynC22UqjNppWQm_jONJ1WoQRxbz_BOC3QMPS8zLNgJ5DQZaxgRToSfdfGRKkGIDEdJDbiZXkFBF8E5uHQBv7Ydj4vcPUaa.riAlhgIOfgmIxxyjLaVE9B_RxVLk_nJK1W5r273wGH63mVobVA;'
}

url = 'https://vidrama.asia/watch/dubbingsopir-taksi-mantan-dewa-balap--846959/1?provider=shortmax'

payloads = [
    '["shortmax","dubbingsopir-taksi-mantan-dewa-balap--846959",1]',
    '["shortmax","dubbingsopir-taksi-mantan-dewa-balap--846959","1"]',
    '["dubbingsopir-taksi-mantan-dewa-balap--846959",1,"shortmax"]',
    '[1,"dubbingsopir-taksi-mantan-dewa-balap--846959","shortmax"]',
    '["dubbingsopir-taksi-mantan-dewa-balap--846959",1]'
]

for p in payloads:
    print(f"\nTesting payload: {p}")
    r = requests.post(url, headers=headers, data=p)
    print(f"Status: {r.status_code}")
    print(r.text[:300])

