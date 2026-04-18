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
    print("ERROR: ADMIN_API_KEY tidak ditemukan")
    exit(1)

payload = {
    "title": "💰 Cepat! Koin Gratis-mu Hari Ini Sudah Siap Klaim!",
    "body": "Bypass Test: Jangan lupa login dan cek tab hadiah ya!",
    "type": "coin_reward",
    "imageUrl": "https://cdn3d.iconscout.com/3d/premium/thumb/gold-coin-4990924-4158914.png"
}

print(f"Mengirim Push Notification KOIN REWARD ke API Broadcast...")
res = requests.post(
    "https://api.shortlovers.id/api/notifications/broadcast",
    headers={"X-Admin-Key": api_key, "Content-Type": "application/json"},
    json=payload
)

if res.status_code == 200:
    data = res.json()
    print(f"BERHASIL TIBA !!")
else:
    print(f"GAGAL! Kode {res.status_code}")
