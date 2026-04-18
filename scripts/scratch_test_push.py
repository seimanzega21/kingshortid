import os
import requests
import time

env_path = os.path.join("d:\\kingshortid", 'cf-backend', '.env.production')
api_key = None
try:
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('ADMIN_API_KEY='):
                api_key = line.strip().split('=', 1)[1]
                break
except Exception as e:
    pass

if not api_key:
    print("❌ ERROR: ADMIN_API_KEY tidak ditemukan")
    exit(1)

# Fetch drama
dramas = []
try:
    res = requests.get("https://api.shortlovers.id/api/dramas?limit=5&page=1")
    dramas = res.json().get('dramas', [])
except:
    pass

if not dramas:
    print("Gagal mengambil drama")
    exit(1)

drama = dramas[0]

payload = {
    "title": f"🚀 TEST PUSH OTA: {drama.get('title')}!",
    "body": "Bypass Splash Screen Test - Coba Klik Sekarang!",
    "imageUrl": drama.get('cover', ''),
    "dramaId": drama.get('id'),
    "episodeNumber": "1",
    "type": "new_episode"
}

print(f"Mengirim Push Notification TEST ke API Broadcast...")
res = requests.post(
    "https://api.shortlovers.id/api/notifications/broadcast",
    headers={"X-Admin-Key": api_key, "Content-Type": "application/json"},
    json=payload
)

if res.status_code == 200:
    data = res.json()
    print(f"✅ BERHASIL !!")
    print(f"  🔔 Terkirim Notif Pop-up (FCM): {data.get('push', {}).get('sent', 0)} HP Android")
    if data.get('push', {}).get('failed', 0) > 0:
        print(f"  ⚠️ Token Expired/Gagal: {data.get('push', {}).get('failed', 0)}")
        print("  [!] Error:", data.get('push', {}).get('errors', []))
else:
    print(f"❌ GAGAL! Kode {res.status_code}")
    print(res.text)
