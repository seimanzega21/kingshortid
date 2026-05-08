import requests

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
HEADERS = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

# ID Drama dari output terminal kamu sebelumnya
DRAMA_ID = 'w6pwucz8bgm8nv9lf8uv52xv'

# Cover R2 yang benar
NEW_COVER = 'https://stream.shortlovers.id/netshortv2/dua-kuasa-menjadi-satu/cover.webp'

print(f"Memperbaiki cover untuk drama ID: {DRAMA_ID}")
print(f"Cover baru: {NEW_COVER}")

try:
    url = f"{API_BASE}/admin/dramas/{DRAMA_ID}"
    r = requests.patch(url, headers=HEADERS, json={'cover': NEW_COVER})
    
    if r.status_code == 200:
        print("BERHASIL! Cover sudah diperbarui menggunakan API.")
        print("Silakan restart aplikasi mobile kamu.")
    else:
        print(f"GAGAL: {r.status_code} - {r.text}")
except Exception as e:
    print(f"Error: {e}")
