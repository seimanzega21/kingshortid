import requests, re

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

def register_properly():
    targets = [
        {"id": "2050068409973997569", "title": "Raja yang Ditakuti Musuh", "episodes": 82},
        {"id": "2033798825713336321", "title": "Menghabisi yang Jahat", "episodes": 91},
        {"id": "2020778605549871106", "title": "Dua Kuasa Menjadi Satu", "episodes": 102}
    ]
    
    for t in targets:
        print(f"Registering: {t['title']}")
        # Using the endpoint verified from scrape_vidrama_standalone.py
        payload = {
            'title': t['title'],
            'description': t['title'],
            'cover': f"https://stream.shortlovers.id/netshortv2/{t['title'].lower().replace(' ', '-')}/cover.jpg",
            'genres': ['Action', 'Drama'],
            'totalEpisodes': t['episodes'],
            'status': 'ongoing',
            'country': 'China',
            'language': 'Indonesia',
            'isActive': False
        }
        r = requests.post(f"{API_BASE}/api/admin/dramas", headers=ADMIN_HDR, json=payload)
        if r.ok:
            new_id = r.json().get('id')
            print(f"  SUCCESS! ID: {new_id}")
        else:
            print(f"  FAILED: {r.status_code} {r.text}")

if __name__ == "__main__":
    register_properly()
