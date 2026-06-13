# -*- coding: utf-8 -*-
import requests, json

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

title = "Dewa yang turun dari gunung"
payload = {
    'title': title,
    'description': "Test description",
    'coverUrl': "https://stream.shortlovers.id/dramas/dewa-yang-turun-dari-gunung/cover.jpg",
    'verticalCoverUrl': "https://stream.shortlovers.id/dramas/dewa-yang-turun-dari-gunung/cover.jpg",
    'totalEpisodes': 60,
    'status': 'Pending',
    'isActive': False,
    'originCountry': 'China',
    'subtitleLanguage': 'Indonesia'
}

r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
print(f"Status Code: {r.status_code}")
print(f"Response Text: {r.text}")
