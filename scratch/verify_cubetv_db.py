import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

# CubeTV titles we expect
expected_titles = [
    "Hubungan Berbahaya",
    "Siapa seret utusan hantu?",
    "Perangkap Cinta yang Salah",
    "Suami yang Mengintip",
    "Zona Dewa-Iblis: Penjaga Terakhir",
    "Qilin sampah? Kembalikan hadiah!",
    "Jahat mikir tak apa, bodoh ide tiba-tiba bahaya",
    "Musim Panas Tak Terdugaku",
    "Perintah yang Tak Tertahankan",
    "Godaan Berbahaya",
    "Tubuh Istri yang Terbangun",
    "Adik Perempuanku Streamer",
    "Sang Bijak Bela Diri Tertinggi",
    "Tak Berbekas"
]

print("=== VERIFYING CUBETV DRAMAS IN DATABASE (COMBINED SEARCH) ===")
found_count = 0
for title in expected_titles:
    found = False
    
    # Method 1: Check public active search
    try:
        r = requests.get(f"{API_BASE}/dramas/search?q={title}", timeout=10)
        dramas = r.json().get('dramas', [])
        for d in dramas:
            if d['title'].lower().strip() == title.lower().strip():
                print(f"[FOUND-ACTIVE] '{d['title']}' (ID: {d['id']}, Active: {d.get('isActive')})")
                r_eps = requests.get(f"{API_BASE}/dramas/{d['id']}?includeInactive=true", timeout=10)
                if r_eps.ok:
                    d_detail = r_eps.json()
                    episodes = d_detail.get('episodes', [])
                    print(f"   - Total episodes in DB: {len(episodes)} / {d_detail.get('totalEpisodes')}")
                found = True
                found_count += 1
                break
    except Exception as e:
        pass

    # Method 2: Check including inactive search if not found yet
    if not found:
        try:
            r = requests.get(f"{API_BASE}/dramas?search={title}&includeInactive=true", timeout=10)
            dramas = r.json()
            if isinstance(dramas, dict):
                dramas = dramas.get('dramas', dramas.get('data', []))
            for d in dramas:
                if d['title'].lower().strip() == title.lower().strip():
                    print(f"[FOUND-PENDING] '{d['title']}' (ID: {d['id']}, Active: {d.get('isActive')})")
                    r_eps = requests.get(f"{API_BASE}/dramas/{d['id']}?includeInactive=true", timeout=10)
                    if r_eps.ok:
                        d_detail = r_eps.json()
                        episodes = d_detail.get('episodes', [])
                        print(f"   - Total episodes in DB: {len(episodes)} / {d_detail.get('totalEpisodes')}")
                    found = True
                    found_count += 1
                    break
        except Exception as e:
            pass

    if not found:
        print(f"[NOT FOUND] '{title}'")

print(f"\nVerification summary: Found {found_count} out of {len(expected_titles)} dramas.")
