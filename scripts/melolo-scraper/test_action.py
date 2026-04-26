import requests
import json
import urllib.parse

url = 'https://vidrama.asia/watch/dubbingsopir-taksi-mantan-dewa-balap--846959/1'

headers = {
    'accept': 'text/x-component',
    'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'text/plain;charset=UTF-8',
    'next-action': '608cb6ff9c19dd8c5454a1f2782fc7baa0e774a348',
    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; HstCnv5004644=26; HstCns5004644=29; panoramaId_expiry=1777275977659; cf_clearance=da_XzER9EpsQhMtP9b.sVZGNd7aLyClwY_F9bCUpRJ0-1777189787-1.2.1.1-GEkPqyfpXxAyNLTe5TTrTdSAFrTO4a4ZBWTnFvlahImB4zpo.dJKEuIrQq4tZGEqCVPMdgSOKQQSsUAOfyr1F4.s7DsCxZWedMKyn2vlm0E6DOzips9vCzxDp7XkmBf9KT2bLVwwMCSx3Mm3RzrGCKQPggbN8d7Ql3Agfo_yanbv.5fZvEnXLeqaCPzalFyNAQIHIynC22UqjNppWQm_jONJ1WoQRxbz_BOC3QMPS8zLNgJ5DQZaxgRToSfdfGRKkGIDEdJDbiZXkFBF8E5uHQBv7Ydj4vcPUaa.riAlhgIOfgmIxxyjLaVE9B_RxVLk_nJK1W5r273wGH63mVobVA; HstCla5004644=1777189787321; HstPn5004644=2; HstPt5004644=62; _ga_HCQQPKGEVH=GS2.1.s1777189572$o61$g1$t1777190339$j58$l0$h0; ttcsid=1777189566464::Ewo6SmY7fLGpJUuwl4Hz.72.1777190376521.0::1.809719.221189::809572.28.164.782::809739.144.0; ttcsid_D5SNQPRC77UDQTF8A5EG=1777189570728::EGlSWyA206FkvAth_qgh.66.1777190376521.1',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36',
    'origin': 'https://vidrama.asia',
    'referer': 'https://vidrama.asia/watch/dubbingsopir-taksi-mantan-dewa-balap--846959/1?provider=shortmax'
}

data = '["dubbingsopir-taksi-mantan-dewa-balap--846959", 1]'

r = requests.post(url, headers=headers, data=data)
print("Status:", r.status_code)
print(r.text)
