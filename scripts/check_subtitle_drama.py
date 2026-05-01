import requests, json

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

# Data dari screenshot
DRAMA_ID = 'n5b51967v8p93f1atm702mut'
DRAMA_TITLE = 'Tertidur 30 tahun, 3 kakak menyesal'

print(f'=== CEK SUBTITLE: {DRAMA_TITLE} ===')
print(f'Drama ID: {DRAMA_ID}')

# Ambil detail drama
r = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID}", headers=ADMIN_HDR, timeout=20)
if r.ok:
    drama = r.json()
    print(f"Total episodes: {drama.get('totalEpisodes')}")
    print(f"isActive: {drama.get('isActive')}")
else:
    print(f"Gagal ambil detail drama: {r.status_code}")
    drama = None

# Ambil semua episode + subtitle
r2 = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID}/episodes", headers=ADMIN_HDR, timeout=20)
if r2.ok:
    data = r2.json()
    eps = data if isinstance(data, list) else data.get('episodes', [])
    print(f"\nJumlah episode di DB: {len(eps)}")
    
    with_sub = 0
    without_sub = 0
    no_sub_list = []
    
    for ep in eps:
        ep_no = ep.get('episodeNumber')
        subtitles = ep.get('subtitles', [])
        has_sub = len(subtitles) > 0
        
        # Detail subtitle
        sub_langs = [s.get('language','?') for s in subtitles]
        
        if has_sub:
            with_sub += 1
        else:
            without_sub += 1
            no_sub_list.append(ep_no)
        
        # Print first 10 and last 10
        if ep_no <= 10 or ep_no >= len(eps) - 9:
            status = "✅" if has_sub else "❌"
            print(f"  ep{ep_no:02d}: {status} subtitles={len(subtitles)} langs={sub_langs}")
    
    print(f"\n=== RINGKASAN ===")
    print(f"Dengan subtitle: {with_sub}/{len(eps)}")
    print(f"Tanpa subtitle: {without_sub}/{len(eps)}")
    if no_sub_list:
        print(f"Episode tanpa subtitle: {no_sub_list}")
    else:
        print("Semua episode punya subtitle!")
else:
    print(f"Gagal ambil episodes: {r2.status_code}")
