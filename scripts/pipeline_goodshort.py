import os
import json
import re
import time
import requests
import subprocess
import boto3
from botocore.config import Config
from urllib.parse import urljoin
from collections import defaultdict

# --- KONFIGURASI ---
PROVIDER = "goodshortv2"
INPUT_JSON = r"D:\kingshortid\all_dramas.json"
TEMP_DIR = r"D:\Video Drama\temp_sedot"
TARGET_DRAMAS = 50

# Cookie dari check_vidrama.py untuk bypass Cloudflare
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; HstPn5004644=1; cf_clearance=AQRjv4.Cj2nHbg_KLivmkViGOllnwGPpIVkj35_jfKI-1777471778-1.2.1.1-TEdhFr7wBXOwe6l8ybhNx3V3OAO2FmEP81fCwLc_mclcsLHuLye6b0vcwrShIGHIdgmlaY14VoOLGlccyUA11WHrRIEncihkGDwdc8C44c79F_3U4SEVsPeQAtPP.1_v6j.daxeE5gMBUPycNwj8rIn4fxg5dhhxrCsZvPIyDKo0BUWtkSEcjfRXcll7MrK8y3YSM8WhGmqI.PzKcfsFF.006ENmy7BGlLwqjy_QDYg8Y7xuxVKlIr_3ApmsnXItGKvJ2DDt_XQUqh1H5hqKnf50BS4QFNfxQEUeytk94ofP8SYQwlqg1HEIz3BMlJC4OQhzn5m0L6muYtASD.jwaw; HstCla5004644=1777471778959; HstPt5004644=72; HstCnv5004644=31; HstCns5004644=35; panoramaId_expiry=1777558180696; _ga_HCQQPKGEVH=GS2.1.s1777476684$o70$g1$t1777477281$j55$l0$h0; ttcsid_D5SNQPRC77UDQTF8A5EG=1777476683162::JiaNdPsba2GCy8oVLuyE.75.1777477294114.1; ttcsid=1777476683155::c9Pa9Oee_DaSEml_Mj5I.85.1777477294114.0::1.610918.6485::610880.63.113.1122::610008.512.600'
}

# --- CLOUDFLARE R2 KREDENSIAL ---
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
BUCKET_NAME = 'shortlovers'
R2_PUBLIC_URL = 'https://stream.shortlovers.id'

s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, 
                  aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4', retries={'max_attempts': 3}), 
                  region_name='auto')

def create_slug(title, book_id):
    clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower()).strip()
    slug_title = re.sub(r'\s+', '-', clean_title)
    return f"{slug_title}--{book_id}"

def check_r2_exists(prefix):
    # Perbaikan: Hanya skip jika 'ep1.mp4' sudah ada di R2 (agar tidak skip jika hanya cover yang terupload)
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=f"{prefix}ep1.mp4", MaxKeys=1)
        return 'Contents' in response
    except: return False

def upload_to_r2(local_file, r2_key):
    try:
        content_type = 'video/mp4' if local_file.endswith('.mp4') else 'image/jpeg'
        s3.upload_file(local_file, BUCKET_NAME, r2_key, ExtraArgs={'ContentType': content_type})
        return f"{R2_PUBLIC_URL}/{r2_key}"
    except Exception as e:
        print(f"[X] Gagal upload {local_file}: {e}")
        return None

def process_drama(drama, index):
    book_id = drama['id']
    title = drama['title']
    slug = create_slug(title, book_id)
    r2_prefix = f"goodshort/{slug}/"
    
    print(f"\n=======================================================")
    print(f"[{index}/{TARGET_DRAMAS}] MEMPROSES: {title} ({book_id})")
    print(f"=======================================================")
    
    if check_r2_exists(r2_prefix):
        print(f"[!] Drama sudah ada sebagian di R2 ({r2_prefix}). Kita akan FORCE resume/replace!")
        # return None (dimatikan sementara untuk memaksa download ulang/resume)
        
    drama_temp_dir = os.path.join(TEMP_DIR, slug)
    os.makedirs(drama_temp_dir, exist_ok=True)
    
    print("[2] Mengambil Data Episode & Metadata Tambahan...")
    ep_map = {}
    cover_url = drama.get('cover')
    
    # Ambil Metadata (Cover, Deskripsi, Genre) langsung dari API Vidrama
    try:
        api_url = f"https://vidrama.asia/api/netshortv2/detail/{book_id}?provider={PROVIDER}&lang=id_ID"
        r_api = requests.get(api_url, headers=WEB_HDRS, timeout=10)
        data = r_api.json().get('data', {})
        if data:
            if not cover_url: cover_url = data.get('cover')
            if not drama.get('description'): drama['description'] = data.get('description', '')
            if data.get('labels'): drama['genres'] = data.get('labels')
            if 'episodes' in data:
                for ep in data['episodes']:
                    ep_map[ep.get('episodeNo') or ep.get('order')] = ep['id']
    except Exception as e:
        print(f"[-] Gagal mengambil metadata: {e}")

    # KARENA VIDRAMA MENYEMBUNYIKAN DAFTAR EPISODE GOODSHORTV2 DARI RSC,
    # DAN KITA TAHU EPISODE 1 UNTUK DRAMA INI ADALAH 18094613,
    # KITA GUNAKAN METODE BRUTE-FORCE BERURUTAN!
    if book_id == '31001370470':
        start_id = 18094613
        # Drama ini memiliki total 90 episode
        for i in range(90):
            ep_map[i + 1] = start_id + i
            
    if not ep_map:
        print("[X] Gagal mengekstrak ID Episode yang valid.")
        return None
        
    ep_ids = sorted(ep_map.items())
    episodes = [{'order': k, 'id': v} for k, v in ep_ids]
        
    print(f"[+] Ditemukan {len(episodes)} Episode. Mulai Proses...")
    
    # Download Cover HD jika tadi ditemukan dari API
    cover_path = os.path.join(drama_temp_dir, 'cover.jpg')
    if cover_url:
        print(f"[*] Mendownload Cover HD: {cover_url[:50]}...")
        try:
            cr = requests.get(cover_url, timeout=10)
            with open(cover_path, 'wb') as f: f.write(cr.content)
            upload_to_r2(cover_path, f"{r2_prefix}cover.jpg")
        except: pass
    
    db_episodes = []
    
    for ep in episodes:
        ep_no = ep['order']
        ep_id = ep['id']
        
        # --- SMART FAST-RESUME ---
        # Cek apakah episode ini sudah ada di R2 secara real-time
        try:
            r2_check_url = f"{R2_PUBLIC_URL}/{r2_prefix}ep{ep_no}.mp4"
            if requests.head(r2_check_url, timeout=5).status_code == 200:
                print(f"  -> Eps {ep_no} SUDAH ADA DI R2! (Resume/Lewati Download)")
                db_episodes.append({
                    "number": ep_no,
                    "url_720p": f"{R2_PUBLIC_URL}/{r2_prefix}ep{ep_no}.mp4",
                    "url_540p": f"{R2_PUBLIC_URL}/{r2_prefix}ep{ep_no}_540p.mp4"
                })
                continue
        except: pass
        # -------------------------
        
        m3u8_url = f"https://vidrama.asia/api/gs2-proxy/m3u8/{ep_id}?bookId={book_id}"
        
        # Validasi M3U8 (agar FFmpeg tidak error 5XX jika episode mati)
        try:
            check = requests.get(m3u8_url, headers=WEB_HDRS, timeout=5)
            if check.status_code != 200 or "EXTM3U" not in check.text:
                print(f"  -> Eps {ep_no} Gagal (HTTP {check.status_code}): {check.text[:100].strip()}")
                continue
        except Exception as e:
            print(f"  -> Eps {ep_no} Timeout: {str(e)[:50]}")
            continue
        
        print(f"\n  -> Sedot & Encode Eps {ep_no} (ID: {ep_id})...")
        file_720p = os.path.join(drama_temp_dir, f"ep{ep_no}_720p.mp4")
        file_540p = os.path.join(drama_temp_dir, f"ep{ep_no}_540p.mp4")
        
        cmd_720 = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-headers", f"Referer: https://vidrama.asia/\r\nCookie: {WEB_HDRS['Cookie']}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n",
            "-i", m3u8_url,
            "-vf", "scale=-2:720", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
            "-c:a", "aac", "-b:a", "128k", file_720p
        ]
        
        cmd_540 = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", file_720p,
            "-vf", "scale=-2:540", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
            "-c:a", "copy", file_540p
        ]
        
        try:
            print("     - Encoding 720p...")
            subprocess.run(cmd_720, check=True)
            print("     - Encoding 540p...")
            subprocess.run(cmd_540, check=True)
            
            print("     - Uploading ke R2...")
            url_720 = upload_to_r2(file_720p, f"{r2_prefix}ep{ep_no}.mp4")
            url_540 = upload_to_r2(file_540p, f"{r2_prefix}ep{ep_no}_540p.mp4")
            
            if url_720:
                db_episodes.append({
                    "number": ep_no,
                    "url_720p": url_720,
                    "url_540p": url_540
                })
                # Hapus file lokal untuk hemat memori
                os.remove(file_720p)
                os.remove(file_540p)
                
        except Exception as e:
            print(f"     [X] Error di Eps {ep_no}: {e}")
            
    if not db_episodes:
        return None
        
    drama_data = {
        "title": title,
        "description": drama.get('description', ''),
        "genres": drama.get('genres', ["Drama", "Romance"]),
        "cover": f"{R2_PUBLIC_URL}/{r2_prefix}cover.jpg",
        "totalEpisodes": len(db_episodes),
        "episodes": db_episodes
    }
    
    return drama_data

def discover_goodshort_dramas():
    print("Mencari Daftar Drama Goodshortv2 dari Vidrama...")
    slugs = set()
    
    # 1. Coba fetch dari Homepage
    try:
        r = requests.get("https://vidrama.asia/?provider=goodshortv2&lang=in", headers=WEB_HDRS, timeout=10)
        # Cari slug dengan pola 10-12 digit (Khas Goodshortv2)
        found = re.findall(r'(?:"|\\")slug(?:"|\\")\s*:\s*(?:"|\\")([a-z0-9\-]+--\d{10,12})(?:"|\\")', r.text)
        slugs.update(found)
    except: pass
    
    # 2. Coba fetch dari Sitemap (Untuk mendapatkan semua list)
    try:
        r = requests.get("https://vidrama.asia/sitemap.xml", headers=WEB_HDRS, timeout=10)
        if "sitemap" in r.text:
            # Ambil semua URL yang ada di sitemap
            found = re.findall(r'watch/([a-z0-9\-]+--\d{10,12})', r.text)
            slugs.update(found)
            
            # Jika ada sub-sitemap
            subs = re.findall(r'<loc>(https://vidrama\.asia/sitemap[^<]+)</loc>', r.text)
            for sub in subs:
                try:
                    rs = requests.get(sub, headers=WEB_HDRS, timeout=10)
                    found_sub = re.findall(r'watch/([a-z0-9\-]+--\d{10,12})', rs.text)
                    slugs.update(found_sub)
                except: pass
    except: pass
    
    dramas = []
    for slug in slugs:
        parts = slug.rsplit('--', 1)
        if len(parts) == 2:
            title = parts[0].replace('-', ' ').title()
            dramas.append({
                'id': parts[1],
                'title': title,
                'slug': slug
            })
            
    print(f"[✓] Berhasil menemukan {len(dramas)} Drama Goodshortv2!")
    return dramas

def main():
    print("=== STARTING PIPELINE GOODSHORT (SINGLE TARGET) ===")
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Fokus 1 drama saja sesuai permintaan
    dramas = [{'id': '31001370470', 'title': 'Penyesalan Tiada Akhir', 'slug': 'penyesalan-tiada-akhir--31001370470'}]
    
    results = []
    out_file = r"D:\kingshortid\goodshort_ingest_data.json"
    if os.path.exists(out_file):
        with open(out_file, 'r', encoding='utf-8') as f:
            try: results = json.load(f)
            except: pass
            
    for i, drama in enumerate(dramas):
        res = process_drama(drama, i + 1)
        if res:
            results.append(res)
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
                
    print("\n[✓] PIPELINE SELESAI!")
    print(f"Data {len(results)} drama siap diinjeksi ke Database.")

if __name__ == "__main__":
    main()
