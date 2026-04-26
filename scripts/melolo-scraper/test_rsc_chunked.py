import requests
import json
import urllib.parse

jwt_token = "eyJhbGciOiJFUzI1NiIsImtpZCI6ImY0NTAxYzU1LTY5ZmMtNDczNy05NzFkLTU1OTVjZmRmZDAwNSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2drY25ibmxmcWRsb3RuamFpenh4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI2ZjNlNWMxNS1hMjFjLTRkMTAtYjg2Yy1lODgxNzBlN2I3MmQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc3MTkzMzg2LCJpYXQiOjE3NzcxODk3ODYsImVtYWlsIjoic2VpbWFuemVnYTIxQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSIsImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImF2YXRhcl91cmwiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NMT2MwbkFudS01bTcxbmNqRjQ0cDJ0dWJ5cUVjRktVTVg5T25pZW1tX1p3TEdJTVJtdz1zOTYtYyIsImVtYWlsIjoic2VpbWFuemVnYTIxQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmdWxsX25hbWwiOiJzZWltYW4gemVnYSIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJzZWltYW4gemVnYSIsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NMT2MwbkFudS01bTcxbmNqRjQ0cDJ0dWJ5cUVjRktVTVg5T25pZW1tX1p3TEdJTVJtdz1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTExODcyOTEzNTI0NDY1MTU0Njg3Iiwic3ViIjoiMTExODcyOTEzNTI0NDY1MTU0Njg3In0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoib2F1dGgiLCJ0aW1lc3RhbXAiOjE3NzcxODk3ODZ9XSwic2Vzc2lvbl9pZCI6ImE4YWRiMmQ5LTM1NDQtNDk5OC04ZmViLWNkNjY1ZDY1YzI0NiIsImlzX2Fub255bW91cyI6ZmFsc2V9.jO_nQ5DCLqRkEclv_8D1U631lCq8TjC3zS39nN8E4jJntYp66aYf4XQzZt8yS7iQ9W7u0Jp5pM8JbJ_bQjL0Bw"
sb_cookie_data = json.dumps([{
    "access_token": jwt_token,
    "token_type": "bearer",
    "expires_in": 3600,
    "expires_at": 1777193386,
    "refresh_token": "dummy",
    "user": {
        "id": "6f3e5c15-a21c-4d10-b86c-e88170e7b72d",
        "role": "authenticated"
    }
}])
encoded_sb = urllib.parse.quote(sb_cookie_data)

chunk_size = 3180
chunks = [encoded_sb[i:i+chunk_size] for i in range(0, len(encoded_sb), chunk_size)]
cookie_parts = []
for i, chunk in enumerate(chunks):
    cookie_parts.append(f"sb-gkcnbnlfqdlotnjaizxx-auth-token.{i}={chunk}")

cookie_string = "; ".join(cookie_parts) + "; cf_clearance=da_XzER9EpsQhMtP9b.sVZGNd7aLyClwY_F9bCUpRJ0-1777189787-1.2.1.1-GEkPqyfpXxAyNLTe5TTrTdSAFrTO4a4ZBWTnFvlahImB4zpo.dJKEuIrQq4tZGEqCVPMdgSOKQQSsUAOfyr1F4.s7DsCxZWedMKyn2vlm0E6DOzips9vCzxDp7XkmBf9KT2bLVwwMCSx3Mm3RzrGCKQPggbN8d7Ql3Agfo_yanbv.5fZvEnXLeqaCPzalFyNAQIHIynC22UqjNppWQm_jONJ1WoQRxbz_BOC3QMPS8zLNgJ5DQZaxgRToSfdfGRKkGIDEdJDbiZXkFBF8E5uHQBv7Ydj4vcPUaa.riAlhgIOfgmIxxyjLaVE9B_RxVLk_nJK1W5r273wGH63mVobVA;"

url = 'https://vidrama.asia/watch/dubbingsopir-taksi-mantan-dewa-balap--846959/11'

headers = {
    'accept': 'text/x-component',
    'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'text/plain;charset=UTF-8',
    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'cookie': cookie_string,
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36',
    'origin': 'https://vidrama.asia',
    'referer': 'https://vidrama.asia/watch/dubbingsopir-taksi-mantan-dewa-balap--846959/11?provider=shortmax',
    'next-action': '608cb6ff9c19dd8c5454a1f2782fc7baa0e774a348'
}

p = '["dubbingsopir-taksi-mantan-dewa-balap--846959",11]'

r = requests.post(url, headers=headers, data=p)
with open('d:\\kingshortid\\scripts\\melolo-scraper\\rsc_output.txt', 'w', encoding='utf-8') as f:
    f.write(r.text)
print("Saved to rsc_output.txt")
