#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Auto-Scraper Vidrama -> R2 -> Database
=============================================
RUN INSTRUCTIONS:
python scripts\batch_scrape_vidrama.py

Fitur:
1. Menyedot daftar spesifik yang diminta.
2. Otomatis mencari judul-judul lain (Auto-Discovery) di beranda Vidrama bahasa Indonesia.
3. Melewati judul yang sudah ada di database (Anti-Duplikat).
"""
import requests, boto3, subprocess, time, tempfile, urllib3, re, os
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── CONFIG ───────────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'

WEB_HDRS    = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; global_ui_lang=id; cf_clearance=gi8rBDL4U_sV5dFUP.Dckjr.DONUzFar9fJlBMJx5_c-1778228148-1.2.1.1-rcSC4qbKF5H0KxB5Zt6Ic88iCIyXH7DESdcJA5w9WLWZvk58Y70clfcHFfqOyxmSRb1I97eRy.96PRr0zF1vV_PWs7vWkLZg2IsJNYLl5ZJvxdv7AnK4pZgxEBspgbrAod7jxce171vMiENcKPDXk_1eVFpBk_P5H8TA07xIBdq5HsL3uPTZKn8BCJv.HufjCR4mRr3DVOGDRagaNcc1CD_VmnRYY6tkanYH9QuDUyPeqreywRNxjb_5tsJVseZjz24po7Gw9o9ZVi3mSl9Ypm88Po1s4zr5n3DfE5R4BCKekPgqBAog2SDMQmDCWQJjMpzKKsJ_iXUHRaincYv9WQ; HstCnv5004644=43; HstCns5004644=47; panoramaId_expiry=1778314550106; HstCla5004644=1778228186632; HstPn5004644=2; HstPt5004644=85; _ga_HCQQPKGEVH=GS2.1.s1778254581$o93$g1$t1778255275$j47$l0$h0; ttcsid=1778254562634::VcwgkELj7wu61kAQZ9m6.110.1778255284779.0::1.721869.41379::721754.142.108.1170::721919.457.0; ttcsid_D5SNQPRC77UDQTF8A5EG=1778254578670::ru6ctqp2kzVRkgnn0scK.94.1778255284779.1'
}

# DAFTAR PRIORITAS MANUAL (Permintaan User)
MANUAL_TARGETS = [
    {'id': '2029132719803334658', 'slug': 'penebusan-sang-tabib'},
    {'id': '2049033017741017090', 'slug': 'istri-pewaris-yang-ditakuti'},
    {'id': '1918527325729849346', 'slug': 'dewa-biliar'},
    {'id': '1985174871400595458', 'slug': 'tebus-langit'},
    {'id': '1953357739876122626', 'slug': 'jangan-kira-dia-polos'},
    {'id': '2038878546117525506', 'slug': 'menghabisi-yang-jahat'},
    {'id': '2020778605818306562', 'slug': 'penjahat-nomor-satu'}
]

TEMP_DIR = Path(tempfile.gettempdir()) / 'ns2_batch_scraper'
TEMP_DIR.mkdir(exist_ok=True)

# ── Helpers ──────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_exists(r2, key):
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

def r2_upload(r2, local_path, key, content_type='video/mp4'):
    r2.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={'ContentType': content_type},
                    Config=boto3.s3.transfer.TransferConfig(multipart_threshold=30*1024*1024, multipart_chunksize=10*1024*1024))
    return f"{R2_PUBLIC}/{key}"

def check_duplicate_in_db(title):
    try:
        r = requests.get(f"{API_BASE}/dramas/search?q={title}", timeout=10)
        dramas = r.json().get('dramas', [])
        for d in dramas:
            if d['title'].lower().strip() == title.lower().strip():
                return d['id']
    except: pass
    return None

def slugify(text):
    text = text.lower()
    return re.sub(r'[\W_]+', '-', text).strip('-')

def get_episode_url(drama_id, ep_no, retries=3):
    url = f"{VIDRAMA_API}/episode/{drama_id}/{ep_no}?lang=id_ID"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
            data = r.json()
            if data.get('code') == 200:
                videos = data['data'].get('videos', [])
                subs = data['data'].get('subtitles', [])
                id_sub = next((s['url'] for s in subs if s.get('language') == 'id_ID'), None)
                if not id_sub and subs: id_sub = subs[0]['url']
                best_video = None
                for q in ['720p', '1080p', '540p']:
                    for v in videos:
                        if v.get('quality') == q:
                            best_video = v['url']
                            break
                    if best_video: break
                if not best_video and videos: best_video = videos[0]['url']
                return best_video, id_sub
        except: time.sleep(2)
    return None, None

def api_get_or_create_drama(detail, slug, cover_url):
    title = detail.get('title', 'Unknown Title')
    payload = {
        'title': title,
        'description': detail.get('description', title),
        'cover': cover_url,
        'genres': detail.get('labels', ['Drama']) or ['Drama'],
        'totalEpisodes': detail.get('totalEpisodes', 0),
        'isComplete': detail.get('isFinished', False),
        'country': 'China', 'language': 'Indonesia',
        'status': 'completed' if detail.get('isFinished') else 'ongoing',
        'isActive': False, # Pending!
    }
    r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
    return r.json().get('id') if r.ok else None

def api_upsert_episode(drama_db_id, ep_no, url_720, url_540=None, sub_url=None):
    payload = {'episodeNumber': ep_no, 'title': f'Episode {ep_no}', 'videoUrl': url_720, 'isActive': True}
    if url_540: payload['videoUrl540p'] = url_540
    r = requests.post(f"{API_BASE}/admin/dramas/{drama_db_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
    if not r.ok: return None
    ep_id = r.json().get('id')
    if ep_id and sub_url:
        sub_payload = {'language': 'indonesia', 'label': 'Indonesia', 'url': sub_url, 'isDefault': True}
        requests.post(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload, timeout=10)
    return ep_id

def encode_720_and_540(inp, out_720, out_540):
    cmd = ['ffmpeg', '-y', '-i', str(inp), '-c:v', 'libx264', '-crf', '26', '-maxrate', '1500k', '-bufsize', '3000k',
           '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-loglevel', 'error', str(out_720)]
    res = subprocess.run(cmd, timeout=600)
    if res.returncode != 0: return False
    cmd3 = ['ffmpeg', '-y', '-i', str(out_720), '-vf', 'scale=-2:540', '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-loglevel', 'error', str(out_540)]
    return subprocess.run(cmd3, timeout=600).returncode == 0

def fetch_auto_discovery_list():
    """Mengambil daftar drama berbahasa Indonesia terbaru dari Beranda Vidrama dan Pencarian"""
    print("\n--- AUTO DISCOVERY: Mencari drama-drama baru berbahasa Indonesia ---")
    discovered = []
    
    # 1. Coba dari Beranda
    try:
        r = requests.get(f"{VIDRAMA_API}/home?lang=id_ID", headers=WEB_HDRS, timeout=15, verify=False)
        json_resp = r.json()
        data = json_resp.get('data') or {}
        modules = data.get('modules') or []
        for mod in modules:
            for item in (mod.get('items') or []):
                vid_id = str(item.get('id', ''))
                title = item.get('title', '')
                if vid_id and title:
                    discovered.append({'id': vid_id, 'title': title, 'slug': slugify(title)})
    except Exception as e:
        print(f"Gagal memindai beranda: {e}")

    # 2. Coba dari Pencarian menggunakan kata kunci Indonesia yang sangat umum di judul Vidrama
    keywords = ["cinta", "suami", "istri", "bos", "kaya", "menantu", "balas dendam", "presiden"]
    print(f"Memindai kata kunci populer: {', '.join(keywords)}...")
    for kw in keywords:
        try:
            r = requests.get(f"{VIDRAMA_API}/search?keyword={kw}&page=1&size=20", headers=WEB_HDRS, timeout=10, verify=False)
            items = r.json().get('data', {}).get('list', [])
            for item in items:
                vid_id = str(item.get('id', ''))
                title = item.get('title', '')
                if vid_id and title:
                    discovered.append({'id': vid_id, 'title': title, 'slug': slugify(title)})
        except: pass

    # Remove duplicates within the discovered list
    unique_discovered = {v['id']:v for v in discovered}.values()
    print(f"Berhasil menemukan {len(unique_discovered)} judul potensial.")
    return list(unique_discovered)

def scrape_single_drama(r2, vidrama_id, slug, provided_title=None):
    prefix = f"netshortv2/{slug}"
    
    # Ambil Metadata
    detail_r = requests.get(f"{VIDRAMA_API}/detail/{vidrama_id}?lang=id_ID", headers=WEB_HDRS, timeout=15, verify=False)
    if not detail_r.ok or detail_r.json().get('code') != 200:
        print(f"[ERROR] Gagal mengambil metadata untuk ID {vidrama_id}.")
        return False
        
    detail = detail_r.json()['data']
    title = detail.get('title', provided_title or 'Unknown')
    total_eps = detail.get('totalEpisodes', 0)
    
    print(f"\n[DRAMA] Memulai proses: {title} ({vidrama_id}) - {total_eps} Episode")
    
    # Pengecekan Bahasa & Duplikat
    lang = detail.get('language', '').lower()
    
    is_manual = any(m['id'] == str(vidrama_id) for m in MANUAL_TARGETS)
    
    # Jika bukan target manual dan kolom bahasanya terisi (tapi bukan bahasa Indonesia), maka kita lewati
    if not is_manual and lang and not ('id' in lang or 'indo' in lang):
        print(f"  -> BUKAN BAHASA INDONESIA (Language: {lang}). Skip!")
        return False
        
    db_id = check_duplicate_in_db(title)
    if db_id:
        if is_manual:
            print(f"  -> [INFO] Judul '{title}' sudah ada di DB. Melanjutkan proses BACKFILL untuk mengisi episode yang bolong/gagal!")
        else:
            print(f"  -> DUPLIKAT! Judul '{title}' sudah ada di database KingShort. Skip!")
            return False
    else:
        # Buat Drama dengan Cover R2 yang benar (bukan link luar)
        cover_key = f"{prefix}/cover.webp"
        r2_cover_url = f"{R2_PUBLIC}/{cover_key}"
        db_id = api_get_or_create_drama(detail, slug, r2_cover_url)
        if not db_id:
            print("  -> [ERROR] Gagal membuat data di DB.")
            return False
        print(f"  -> [DB] Terdaftar dengan ID: {db_id} (Status: Pending)")

    # Upload Cover Kualitas Tinggi jika belum ada
    cover_key = f"{prefix}/cover.webp"
    if not r2_exists(r2, cover_key):
        try:
            cov = requests.get(detail['cover'], headers=WEB_HDRS, timeout=30, verify=False)
            p = TEMP_DIR / f"{slug}_cov"
            p.write_bytes(cov.content)
            r2_upload(r2, p, cover_key, 'image/webp')
            p.unlink()
        except: pass

    skipped = success = failed = 0
    for ep_no in range(1, total_eps + 1):
        k720 = f"{prefix}/ep{ep_no:03d}.mp4"
        k540 = f"{prefix}/ep{ep_no:03d}_540p.mp4"
        ksub = f"{prefix}/ep{ep_no:03d}.vtt"

        if r2_exists(r2, k720):
            print(f"    ep{ep_no:03d}: SUDAH ADA di R2, skip download...", flush=True)
            u720 = f"{R2_PUBLIC}/{k720}"
            u540 = f"{R2_PUBLIC}/{k540}" if r2_exists(r2, k540) else None
            sub_url = f"{R2_PUBLIC}/{ksub}" if r2_exists(r2, ksub) else None
            api_upsert_episode(db_id, ep_no, u720, u540, sub_url)
            success += 1
            continue

        vurl, sub_url_raw = get_episode_url(vidrama_id, ep_no)
        if not vurl:
            print(f"    [WARN] URL tidak ditemukan untuk ep{ep_no}")
            skipped += 1
            continue

        # Upload Subtitle
        final_sub_r2 = None
        if sub_url_raw:
            try:
                sub_r = requests.get(sub_url_raw, timeout=10, verify=False)
                if sub_r.ok:
                    r2.put_object(Bucket=R2_BUCKET, Key=ksub, Body=sub_r.content, ContentType='text/vtt')
                    final_sub_r2 = f"{R2_PUBLIC}/{ksub}"
            except: pass

        raw = TEMP_DIR / f"{slug}_raw_{ep_no}.mp4"
        o720 = TEMP_DIR / f"{slug}_720_{ep_no}.mp4"
        o540 = TEMP_DIR / f"{slug}_540_{ep_no}.mp4"

        try:
            # Fungsi untuk mendownload dengan retry
            download_success = False
            for dl_attempt in range(3):
                with requests.get(vurl, stream=True, headers=WEB_HDRS, verify=False, timeout=60) as r:
                    if r.status_code == 200:
                        with open(raw, 'wb') as f:
                            for c in r.iter_content(2*1024*1024): 
                                if c: f.write(c)
                        # Pastikan ukuran file masuk akal (minimal 500KB)
                        if raw.exists() and raw.stat().st_size > 500000:
                            download_success = True
                            break
                print(" [RETRY DL]", end="", flush=True)
                time.sleep(3)

            if not download_success:
                print(" [ERROR] Gagal download file utuh dari CDN")
                failed += 1
                continue

            print(f"    ep{ep_no:03d}: Encoding...", end="", flush=True)
            if encode_720_and_540(raw, o720, o540):
                u720 = r2_upload(r2, o720, k720)
                u540 = r2_upload(r2, o540, k540) if o540.exists() else None
                api_upsert_episode(db_id, ep_no, u720, u540, final_sub_r2)
                print(" BERHASIL")
                success += 1
            else:
                print(" [ERROR] Encoding Gagal (File korup/moov atom missing)")
                failed += 1
        except Exception as e:
            print(f" [ERROR] {e}")
            failed += 1
        finally:
            for p in [raw, o720, o540]:
                if p.exists(): p.unlink()

    print(f"  -> SELESAI: {success} sukses, {failed} gagal, {skipped} terlewat.")
    return True

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    r2 = get_r2()
    print("="*60)
    print("🤖 KINGSHORT BATCH & AUTO-DISCOVERY SCRAPER DIMULAI")
    print("="*60)
    
    # 1. Jalankan Target Manual Dulu
    print("\n--- FASE 1: Mengeksekusi Target Prioritas Manual ---")
    for target in MANUAL_TARGETS:
        scrape_single_drama(r2, target['id'], target['slug'])
        
    # 2. Jalankan Auto-Discovery
    auto_targets = fetch_auto_discovery_list()
    for target in auto_targets:
        # Pengecekan awal duplikat untuk menghemat API call Detail
        if check_duplicate_in_db(target['title']):
            print(f"\n[SKIP] '{target['title']}' sudah ada di database.")
            continue
            
        # Pengecekan apakah target id ini sudah di-scrape di fase manual
        if any(m['id'] == target['id'] for m in MANUAL_TARGETS):
            continue
            
        scrape_single_drama(r2, target['id'], target['slug'], provided_title=target['title'])
        
    print("\n" + "="*60)
    print("🎉 SELURUH ANTRIAN SCRAPING BATCH SELESAI!")
    print("Cek Admin Panel untuk melihat judul-judul baru (status Pending).")

if __name__ == "__main__":
    main()
