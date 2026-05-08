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
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; HstPn5004644=1; cf_clearance=AQRjv4.Cj2nHbg_KLivmkViGOllnwGPpIVkj35_jfKI-1777471778-1.2.1.1-TEdhFr7wBXOwe6l8ybhNx3V3OAO2FmEP81fCwLc_mclcsLHuLye6b0vcwrShIGHIdgmlaY14VoOLGlccyUA11WHrRIEncihkGDwdc8C44c79F_3U4SEVsPeQAtPP.1_v6j.daxeE5gMBUPycNwj8rIn4fxg5dhhxrCsZvPIyDKo0BUWtkSEcjfRXcll7MrK8y3YSM8WhGmqI.PzKcfsFF.006ENmy7BGlLwqjy_QDYg8Y7xuxVKlIr_3ApmsnXItGKvJ2DDt_XQUqh1H5hqKnf50BS4QFNfxQEUeytk94ofP8SYQwlqg1HEIz3BMlJC4OQhzn5m0L6muYtASD.jwaw; HstCla5004644=1777471778959; HstPt5004644=72; HstCnv5004644=31; HstCns5004644=35; panoramaId_expiry=1777558180696; _ga_HCQQPKGEVH=GS2.1.s1777476684$o70$g1$t1777477281$j55$l0$h0; ttcsid_D5SNQPRC77UDQTF8A5EG=1777476683162::JiaNdPsba2GCy8oVLuyE.75.1777477294114.1; ttcsid=1777476683155::c9Pa9Oee_DaSEml_Mj5I.85.1777477294114.0::1.610918.6485::610880.63.113.1122::610008.512.600'
}

# DAFTAR PRIORITAS MANUAL (Permintaan User)
MANUAL_TARGETS = [
    {'id': '2044966103939022850', 'slug': 'ceo-cantik-dan-suami-kayanya'},
    {'id': '2049446787831300098', 'slug': 'agenda-sang-pengawal'}
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
                return True
    except: pass
    return False

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
    """Mengambil daftar drama berbahasa Indonesia terbaru dari Homepage/Kategori Vidrama"""
    print("\n--- AUTO DISCOVERY: Mencari drama-drama baru berbahasa Indonesia ---")
    discovered = []
    try:
        r = requests.get(f"{VIDRAMA_API}/home?lang=id_ID", headers=WEB_HDRS, timeout=15, verify=False)
        data = r.json()
        if data.get('code') == 200:
            modules = data.get('data', {}).get('modules', [])
            for mod in modules:
                items = mod.get('items', [])
                for item in items:
                    vid_id = str(item.get('id', ''))
                    title = item.get('title', '')
                    if vid_id and title:
                        discovered.append({
                            'id': vid_id,
                            'title': title,
                            'slug': slugify(title)
                        })
    except Exception as e:
        print(f"Gagal melakukan Auto-Discovery: {e}")
    
    # Remove duplicates within the discovered list
    unique_discovered = {v['id']:v for v in discovered}.values()
    print(f"Berhasil menemukan {len(unique_discovered)} judul potensial dari Beranda Vidrama.")
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
    is_indo = 'id' in lang or 'indo' in lang
    
    if not is_indo:
        print(f"  -> BUKAN BAHASA INDONESIA (Language: {lang}). Skip!")
        return False
        
    if check_duplicate_in_db(title):
        print(f"  -> DUPLIKAT! Judul '{title}' sudah ada di database KingShort. Skip!")
        return False

    db_id = api_get_or_create_drama(detail, slug, detail['cover'])
    if not db_id:
        print("  -> [ERROR] Gagal membuat data di DB.")
        return False
        
    print(f"  -> [DB] Terdaftar dengan ID: {db_id} (Status: Pending)")

    # Upload Cover Kualitas Tinggi
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
            with requests.get(vurl, stream=True, headers=WEB_HDRS, verify=False) as r:
                with open(raw, 'wb') as f:
                    for c in r.iter_content(2*1024*1024): f.write(c)

            print(f"    ep{ep_no:03d}: Encoding...", end="", flush=True)
            if encode_720_and_540(raw, o720, o540):
                u720 = r2_upload(r2, o720, k720)
                u540 = r2_upload(r2, o540, k540) if o540.exists() else None
                api_upsert_episode(db_id, ep_no, u720, u540, final_sub_r2)
                print(" BERHASIL")
                success += 1
            else:
                print(" [ERROR] Encoding Gagal")
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
