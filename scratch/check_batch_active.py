# -*- coding: utf-8 -*-
import requests

api_base = 'https://api.shortlovers.id/api'
title = "Saat Saudari Tiriku Mengulang Waktu"

print(f"Checking if '{title}' has been created in DB...")
try:
    r = requests.get(f"{api_base}/dramas/search?q={title}", timeout=10)
    if r.ok:
        dramas = r.json().get('dramas', [])
        found = False
        for d in dramas:
            if d['title'].lower().strip() == title.lower().strip():
                print(f"FOUND! ID: {d['id']}, isActive: {d.get('isActive')}")
                found = True
                break
        if not found:
            print("Not found in search results yet.")
    else:
        print("Error search status:", r.status_code)
except Exception as e:
    print("Error:", e)
