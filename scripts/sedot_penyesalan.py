import requests
import re
import os
import subprocess

BOOK_ID = "31001370470"
SLUG = "penyesalan-tiada-akhir--31001370470"

# Header untuk mengelabui server agar dikira browser HP
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36',
    'Referer': f'https://vidrama.asia/watch/{SLUG}/1?provider=goodshortv2&lang=in',
    'rsc': '1',
    'sec-ch-ua-platform': '"Android"'
}

def get_episodes():
    print("[1] Mengambil Daftar Episode dari Server...")
    url = f"https://vidrama.asia/watch/{SLUG}/1?provider=goodshortv2&lang=in&_rsc=1cguy"
    
    r = requests.get(url, headers=HEADERS)
    text = r.text
    
    # Mencari semua ID episode dari respon Next.js Server (Biasanya terstruktur dan berdekatan)
    # Trik: Karena kita tahu Episode 1 ID-nya 18094613, kita cari semua angka 8 digit yang mirip
    raw_ids = re.findall(r'(1809\d{4})', text)
    
    if not raw_ids:
        # Jika trik pertama gagal, cari pola generic "id":12345
        raw_ids = re.findall(r'"id":(\d{8,12})', text)
        
    # Hapus duplikat dan urutkan (Episode 1 biasanya ID terkecil, dst)
    ep_ids = sorted(list(set(raw_ids)))
    
    # Filter hanya ID yang masuk akal (mencegah salah tangkap ID buku/drama)
    ep_ids = [eid for eid in ep_ids if eid != BOOK_ID]
    
    if not ep_ids:
        print("[!] Gagal mendapatkan ID Episode. Memakai metode Brute-Force (Berurutan)...")
        # Fallback ke Brute-Force karena kita tahu Episode 1 = 18094613
        ep_ids = [str(18094613 + i) for i in range(100)] # Asumsi maksimal 100 episode
    
    print(f"[+] Ditemukan perkiraan {len(ep_ids)} Episode!")
    return ep_ids

def download_episodes(ep_ids):
    folder_name = "Penyesalan_Tiada_Akhir"
    out_dir = os.path.join(r"D:\Video Drama", folder_name)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    os.chdir(out_dir)
    print(f"\n[2] Memulai Download Video ke: {out_dir}")
    
    for i, ep_id in enumerate(ep_ids):
        ep_num = i + 1
        m3u8_url = f"https://vidrama.asia/api/gs2-proxy/m3u8/{ep_id}?bookId={BOOK_ID}"
        filename = f"Part_{ep_num:02d}.mp4"
        
        # Validasi URL M3U8 sebelum download
        try:
            check = requests.get(m3u8_url, headers={"Referer": "https://vidrama.asia/"}, timeout=5)
            if check.status_code != 200 or "EXTM3U" not in check.text:
                if i > 5: # Jika sudah download beberapa episode lalu gagal, berarti sudah tamat
                    print("\n[+] Sepertinya episode sudah habis. Download Selesai!")
                    break
                continue # Skip jika error di awal (mungkin loncat ID)
        except:
            pass
            
        print(f" -> Sedot Episode {ep_num} (ID: {ep_id}) ...")
        
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-headers", "Referer: https://vidrama.asia/\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n",
            "-i", m3u8_url,
            "-c", "copy",
            filename
        ]
        
        subprocess.run(cmd)
        
        if os.path.exists(filename) and os.path.getsize(filename) > 100000:
            print(f"    [OK] {filename} berhasil didownload!")
        else:
            print(f"    [X] Gagal mendownload {filename}.")

if __name__ == "__main__":
    print("========================================")
    print("   AUTO-DOWNLOADER GOODSHORT VIDRAMA")
    print("========================================")
    episodes = get_episodes()
    if episodes:
        download_episodes(episodes)
    print("\n[SELESAI] Semua proses telah berakhir.")
