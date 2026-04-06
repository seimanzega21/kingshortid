import os
import requests
import json
import time

# Auto-detect ADMIN_API_KEY from cf-backend/.env.production
env_path = os.path.join(os.path.dirname(__file__), '..', 'cf-backend', '.env.production')
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
    print("❌ ERROR: ADMIN_API_KEY tidak ditemukan di .env.production")
    exit(1)

def clr():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_latest_dramas():
    try:
        res = requests.get("https://api.shortlovers.id/api/dramas?limit=10&page=1")
        if res.status_code == 200:
            return res.json().get('dramas', [])
    except Exception as e:
        pass
    return []

while True:
    clr()
    print("==================================================")
    print(" 🚀 KINGSHORT AUTO PUSH BLASTER (MUDAH) 🚀")
    print("==================================================")
    print("Pilih tipe promosi otomatis (tanpa perlu ngetik panjang):")
    print("")
    print("  [1] 🎬 Promosikan Drama Terbaru (Tarik Data Otomatis)")
    print("  [2] 💰 Pengingat Hadiah Koin (Ajak user login otomatis)")
    print("  [3] ✍️ Tulis Pesan Custom Manual")
    print("  [4] 🚪 Keluar")
    print("==================================================")
    
    pilihan = input("Masukkan pilihan angka (1/2/3/4) lalu tekan Enter: ").strip()
    
    if pilihan == '4':
        print("Sampai jumpa!")
        break
        
    payload = {"type": "system"}
    
    if pilihan == '1':
        print("\n⏳ Mengambil daftar drama terbaru dari server secara otomatis...")
        dramas = get_latest_dramas()
        if not dramas:
            print("Gagal mengambil drama. Pastikan internet jalan.")
            time.sleep(2)
            continue
            
        print("\nSilakan Pilih Drama yang mau diviralkan (Notifikasi dikirim otomatis bergambar cover):")
        for idx, d in enumerate(dramas):
            print(f"  [{idx+1}] {d.get('title')}")
            
        try:
            d_idx = int(input("\nMasukkan angka drama pilihanmu: ").strip()) - 1
            selected = dramas[d_idx]
        except:
            print("Angka tidak valid.")
            time.sleep(1)
            continue
            
        payload['title'] = f"🎉 Sedang Viral: {selected.get('title')}!"
        payload['body'] = "Yuk tonton dramanya sekarang, dijamin bikin baper!"
        payload['imageUrl'] = selected.get('cover', '')
        payload['dramaId'] = selected.get('id')
        payload['episodeNumber'] = "1"
        payload['type'] = "new_episode"
        
    elif pilihan == '2':
        payload['title'] = "💰 Cepat! Koin Gratis-mu Hari Ini Sudah Siap Klaim!"
        payload['body'] = "Jangan lupa login dan tonton tugas harian untuk nonton VIP secara gratis."
        payload['type'] = "coin_reward"
        # Dummy gambar koin
        payload['imageUrl'] = "https://cdn3d.iconscout.com/3d/premium/thumb/gold-coin-4990924-4158914.png" 
        
    elif pilihan == '3':
        print("\n--- MODE MANUAL ---")
        payload['title'] = input("👉 Judul (Wajib): ").strip()
        payload['body'] = input("👉 Isi Pesan (Wajib): ").strip()
        
        if not payload['title'] or not payload['body']:
            print("\n❌ Judul dan isi pesan wajib diisi.")
            time.sleep(2)
            continue
            
        img = input("👉 URL Gambar Besar (Opsional, Enter jika lewat): ").strip()
        if img:
            payload['imageUrl'] = img
            
        dmid = input("👉 ID Drama spesifik yg mau dituju (Opsional, Enter jika lewat): ").strip()
        if dmid:
            payload['dramaId'] = dmid
            payload['episodeNumber'] = "1"
            payload['type'] = "new_episode"
            
    else:
        continue
        
    print("\n" + "="*50)
    print(f"⏳ MENGIRIM NOTIFIKASI KE RATUSAN HP...")
    print(f"Judul : {payload['title']}")
    print(f"Target: Semua User Aktif")
    print("="*50)
    
    try:
        res = requests.post(
            "https://api.shortlovers.id/api/notifications/broadcast",
            headers={
                "X-Admin-Key": api_key,
                "Content-Type": "application/json"
            },
            json=payload
        )
        if res.status_code == 200:
            data = res.json()
            print(f"\n✅ BERHASIL !!")
            print(f"  📱 Terkirim masuk memori aplikasi : {data.get('inApp', 0)} user")
            print(f"  🔔 Terkirim Notif Pop-up (FCM)  : {data.get('push', {}).get('sent', 0)} HP Android")
            
            if data.get('push', {}).get('failed', 0) > 0:
                print(f"  ⚠️ Token Expired/Dihapus User   : {data.get('push', {}).get('failed', 0)} HP")
                
            print("\nSilakan cek layar HP-mu sekarang, notifikasi gambarnya pasti sudah muncul!")
        else:
            print(f"\n❌ GAGAL! Server merespons (Kode {res.status_code}):")
            try:
                print(res.json())
            except:
                print(res.text)
    except Exception as e:
        print(f"\n❌ ERROR Aplikasi: {e}")
        
    input("\nTekan Enter untuk kembali ke Menu Utama...")
