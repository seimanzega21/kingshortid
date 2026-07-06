# -*- coding: utf-8 -*-
import requests
import urllib.parse

cover_url = "https://p16-novel-sign.fizzopic.org/novel-images-apsoutheast/cefa1fc23058ad47863b96fbba24959e~tplv-836v1mcgsk-resize:336:478.heic?rk3s=253f70db&x-expires=1785024371&x-signature=qa2siec1Pz%2BQ3rlQrQ5e8twe%2B2A%3D"
converted_url = f"https://wsrv.nl/?url={urllib.parse.quote(cover_url)}&output=jpg"

r = requests.get(converted_url)
print("Status:", r.status_code)
print(r.text[:1000])
