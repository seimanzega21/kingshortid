# -*- coding: utf-8 -*-
import requests
import urllib.parse

cover_url = "https://p16-novel-sign.fizzopic.org/novel-images-apsoutheast/cefa1fc23058ad47863b96fbba24959e~tplv-836v1mcgsk-resize:336:478.heic?rk3s=253f70db&x-expires=1785024371&x-signature=qa2siec1Pz%2BQ3rlQrQ5e8twe%2B2A%3D"
converted_url = f"https://wsrv.nl/?url={urllib.parse.quote(cover_url)}&output=jpg"

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

print("Querying wsrv.nl with User-Agent...")
r = requests.get(converted_url, headers=WEB_HDRS)
print("Status:", r.status_code)
print("Content type:", r.headers.get('Content-Type'))
print("Content length:", len(r.content))
if r.ok:
    print("Magic bytes:", r.content[:4])
else:
    print(r.text[:500])
