# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://vidrama.asia/_next/static/chunks/123c8307fc6c5765.js'
r = requests.get(url, verify=False)
if r.ok:
    # Let's search for "A =" or "A=" or similar in the chunk
    # Let's search for patterns like `A = r(...)` or `A = n(...)` or `A = o(...)`
    # Let's look for how `A` is assigned.
    # We can also search for where the module containing shortmax is imported.
    # Let's search for `getEpisodeUrl` in the whole file and see if there are other variables called with getEpisodeUrl.
    # In match 1: `A.getEpisodeUrl`
    # Let's print all variables that call `getEpisodeUrl`.
    matches = re.findall(r'(\w+)\.getEpisodeUrl', r.text)
    print("Variables calling getEpisodeUrl:", set(matches))
