import os, sys, time, requests, urllib3, subprocess, shutil, argparse, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.config import Config
import boto3

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_BASE  = 'https://api.shortlovers.id'
R2_PUBLIC = 'https://stream.shortlovers.id'

ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}
WEB_HDRS  = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
BUCKET      = 'shortlovers'

TEMP_DIR    = 'D:/temp_global_scraper'
os.makedirs(TEMP_DIR, exist_ok=True)

def get_r2():
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID,
        aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4', retries={'max_attempts': 3, 'mode': 'standard'}),
        region_name='auto'
    )

def fetch_catalog(provider, limit):
    """
    Menarik daftar drama secara otomatis menggunakan sitemap.xml dari Vidrama.
    """
    print(f"[*] Fetching catalog dari sitemap Vidrama untuk provider: {provider}...")
    try:
        xml = requests.get('https://vidrama.asia/sitemap.xml', headers=WEB_HDRS, verify=False, timeout=15).text
        pattern = rf"<loc>https://vidrama\.asia/movie/([^/]+)--(\d+)\?provider={provider}</loc>"
        matches = re.findall(pattern, xml)
        
        matches = list(set(matches))
        print(f"[*] Ditemukan {len(matches)} drama untuk provider {provider} di sitemap.")
        
        dramas = []
        for slug, vid_id in matches:
            title = slug.replace('-', ' ').title()
            dramas.append({
                'id': vid_id,
                'slug': slug,
                'title': title,
                'genres': ['Populer']
            })
            
        return dramas[:limit]
    except Exception as e:
        print(f"[!] Gagal menarik sitemap: {e}")
        return []

def get_existing_dramas_in_db():
    print("[*] Sinkronisasi dengan database KingShort...")
    try:
        r = requests.get(f"{API_BASE}/api/dramas?limit=5000&includeInactive=true", timeout=15).json()
        dramas = r if isinstance(r, list) else r.get('dramas', [])
        existing_slugs = {d.get('slug', '').lower() for d in dramas}
        return existing_slugs
    except Exception as e:
        print(f"[!] Gagal sinkronisasi DB: {e}")
        return set()

def ensure_drama_sop(d_info, intro, cover_url_r2):
    r = requests.get(f"{API_BASE}/api/dramas?limit=1000&includeInactive=true", timeout=15).json()
    dramas = r if isinstance(r, list) else r.get('dramas', [])
    for d in dramas:
        if d_info['slug'].lower() == d.get('slug', '').lower() or d_info['title'].lower() in d.get('title', '').lower():
            did = d['id']
            print(f"  [*] Drama sudah ada di DB! ID: {did}, memperbarui status...")
            requests.patch(f"{API_BASE}/api/admin/dramas/{did}", headers=ADMIN_HDR, json={'isActive': False, 'status': 'completed'}, timeout=10)
            return did
            
    payload = {
        'title': d_info['title'],
        'description': intro or f"Drama seru: {d_info['title']}",
        'cover': cover_url_r2,
        'status': 'completed',
        'isActive': False, # Default pending
        'genres': d_info['genres']
    }
    rc = requests.post(f"{API_BASE}/api/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
    if rc.ok:
        did = rc.json().get('id')
        print(f"  [+] Berhasil membuat drama di DB! ID: {did}")
        return did
    else:
        raise Exception(f"Gagal membuat drama: {rc.status_code} {rc.text}")

def process_episode_sop(ep_data, drama_id, slug, r2, provider):
    ep_no = int(ep_data.get('index', 0))
    v_url = ep_data.get('stream_url')
    if not v_url:
        return ep_no, False, "No stream_url"
        
    key_720 = f"{provider}/{slug}/ep{ep_no:03d}.mp4"
    key_540 = f"{provider}/{slug}/ep{ep_no:03d}_540p.mp4"
    
    worker_dir = os.path.join(TEMP_DIR, f"{slug}_ep{ep_no:03d}")
    os.makedirs(worker_dir, exist_ok=True)
    out_raw = os.path.join(worker_dir, "raw.mp4")
    out_540 = os.path.join(worker_dir, "540p.mp4")
    
    try:
        cmd_raw = ['ffmpeg', '-y', '-headers', 'Referer: https://vidrama.asia/', '-i', v_url, '-c', 'copy', '-movflags', '+faststart', '-loglevel', 'error', out_raw]
        subprocess.run(cmd_raw, cwd=worker_dir, check=True)
        
        cmd_540 = ['ffmpeg', '-y', '-i', out_raw, '-vf', 'scale=540:-2', '-c:v', 'libx264', '-preset', 'superfast', '-crf', '25', '-c:a', 'copy', '-movflags', '+faststart', '-loglevel', 'error', out_540]
        subprocess.run(cmd_540, cwd=worker_dir, check=True)
        
        with open(out_raw, 'rb') as f:
            r2.upload_fileobj(f, BUCKET, key_720, ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})
            
        f_540 = out_540 if os.path.exists(out_540) else out_raw
        with open(f_540, 'rb') as f:
            r2.upload_fileobj(f, BUCKET, key_540, ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})
            
        t_buster = int(time.time())
        ep_payload = {
            'episodeNumber': ep_no,
            'title': f'Episode {ep_no}',
            'videoUrl': f"{R2_PUBLIC}/{key_720}?v={t_buster}",
            'videoUrl540p': f"{R2_PUBLIC}/{key_540}?v={t_buster}",
            'isVip': False,
            'coinPrice': 0,
            'duration': int(ep_data.get('duration') or 90),
            'coverUrl': f"{R2_PUBLIC}/{provider}/{slug}/cover_hq.jpg",
            'isActive': True
        }
        
        size_mb = os.path.getsize(out_raw) / (1024*1024)
        return ep_no, True, ep_payload, f"OK ({size_mb:.1f} MB)"
    except Exception as e:
        return ep_no, False, None, str(e)[:100]
    finally:
        shutil.rmtree(worker_dir, ignore_errors=True)


def process_single_drama(drama_info, provider, is_dry_run):
    title = drama_info['title']
    vid_id = drama_info['id']
    slug = drama_info['slug']
    print(f"\n>> Memproses Drama: {title} (ID: {vid_id})")
    
    if is_dry_run:
        print(f"   [DRY RUN] Akan disedot jika dry-run dimatikan.")
        return True
        
    r2 = get_r2()
    
    # Ambil detail dari vidrama
    for attempt in range(3):
        try:
            url_api = f"https://vidrama.asia/api/{provider}/multi-video?id={vid_id}&lang=id"
            # Fallback ke melolov3 atau v2 jika provider utamanya melolo
            if provider == 'melolo':
                # coba v3 dulu, jika gagal coba v2
                r_mv = requests.get(f"https://vidrama.asia/api/melolov3/multi-video?id={vid_id}&lang=id", headers=WEB_HDRS, verify=False, timeout=20)
                if r_mv.status_code != 200:
                    r_mv = requests.get(f"https://vidrama.asia/api/melolov2/multi-video?id={vid_id}&lang=id", headers=WEB_HDRS, verify=False, timeout=20)
            else:
                r_mv = requests.get(url_api, headers=WEB_HDRS, verify=False, timeout=20)
                
            r_mv_json = r_mv.json()
            break
        except Exception as e:
            if attempt == 2:
                print(f"   [!] Gagal mengambil info dari Vidrama: {e}")
                return False
            time.sleep(2)
            
    series_info = r_mv_json.get('series', {})
    episodes    = r_mv_json.get('episodes', [])
    desc        = series_info.get('intro', '')
    
    # Update title dengan yg lebih akurat dari API jika ada
    if series_info.get('title'):
        drama_info['title'] = series_info.get('title')
        title = drama_info['title']
        
    print(f"   [*] Ditemukan {len(episodes)} episode di sumbernya.")
    
    # Konversi Cover SOP
    cover_src = series_info.get('cover') or (episodes[0].get('cover') if episodes else None)
    cover_r2_url = f"{R2_PUBLIC}/{provider}/{slug}/cover_hq.jpg"
    
    if cover_src:
        for attempt in range(3):
            try:
                rcov = requests.get(cover_src, headers=WEB_HDRS, verify=False, timeout=15)
                if rcov.ok:
                    raw_cov = os.path.join(TEMP_DIR, f"{slug}_cov.raw")
                    jpg_cov = os.path.join(TEMP_DIR, f"{slug}_cov.jpg")
                    with open(raw_cov, "wb") as f: f.write(rcov.content)
                    subprocess.run(['ffmpeg', '-y', '-i', raw_cov, '-update', '1', '-q:v', '2', jpg_cov], check=True, capture_output=True)
                    with open(jpg_cov, "rb") as f:
                        r2.upload_fileobj(f, BUCKET, f"{provider}/{slug}/cover_hq.jpg", ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'})
                    for tf in [raw_cov, jpg_cov]:
                        if os.path.exists(tf): os.remove(tf)
                    break
            except Exception as e:
                time.sleep(2)
                
    # Daftarkan Drama
    try:
        drama_db_id = ensure_drama_sop(drama_info, desc, cover_r2_url)
    except Exception as e:
        print(f"   [!] Gagal mendaftarkan drama: {e}")
        return False
        
    # Ambil episode yang sudah ada (dengan parameter includeInactive=true agar bisa mengecek status pending)
    d_detail = requests.get(f"{API_BASE}/api/dramas/{drama_db_id}?includeInactive=true", timeout=20).json()
    existing_eps = {e['episodeNumber'] for e in d_detail.get('episodes', [])}
    missing_eps = [ep for ep in episodes if int(ep.get('index', 0)) not in existing_eps]
    
    print(f"   [*] Melanjutkan {len(missing_eps)} episode yang belum ada...")
    
    if not missing_eps:
        print("   [*] Selesai! Semua episode sudah ada.")
        return True

    success_count = 0
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_episode_sop, ep, drama_db_id, slug, r2, provider): ep for ep in missing_eps}
        for future in as_completed(futures):
            ep_no, ok, payload, msg = future.result()
            if ok:
                results.append((ep_no, payload, msg))
                print(f"      [~] [EP {ep_no:02d}] Video sukses ke R2, menunggu antrean DB...", flush=True)
            else:
                print(f"      [-] [EP {ep_no:02d}] Gagal download/R2 ({msg})", flush=True)
                
    # Sort and insert to DB sequentially to maintain order
    results.sort(key=lambda x: x[0])
    print(f"   [*] Menyimpan {len(results)} episode ke database secara berurutan...")
    
    for ep_no, payload, msg in results:
        success = False
        for attempt in range(5):
            rcr = requests.post(f"{API_BASE}/api/admin/dramas/{drama_db_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
            if rcr.ok:
                success = True
                break
            time.sleep(2)
            
        if success:
            success_count += 1
            print(f"      [+] [EP {ep_no:02d}] Sukses disimpan ({msg})", flush=True)
        else:
            print(f"      [-] [EP {ep_no:02d}] Gagal simpan ke DB ({rcr.text})", flush=True)
                
    print(f"   [*] Selesai {title}: {success_count}/{len(missing_eps)} episode diproses.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Global Scraper Auto-Ingestion Pipeline")
    parser.add_argument('--provider', type=str, required=True, help="Kode provider (contoh: melolo, stardusttv)")
    parser.add_argument('--limit', type=int, default=10, help="Maksimal drama yang disedot dalam satu siklus")
    parser.add_argument('--dry-run', action='store_true', help="Hanya mengecek database, tidak mengunduh")
    args = parser.parse_args()

    print("="*70)
    print(f"GLOBAL SCRAPER PIPELINE - Provider: {args.provider}")
    print("="*70)

    # 1. Fetch Catalog
    catalog = fetch_catalog(args.provider, args.limit)
    if not catalog:
        print("[!] Tidak ada katalog yang diproses. Pipeline berhenti.")
        return

    # 2. Database Diffing
    existing_slugs = get_existing_dramas_in_db()
    
    missing_dramas = []
    for d in catalog:
        if d['slug'].lower() not in existing_slugs:
            missing_dramas.append(d)

    print(f"\n[*] Ditemukan {len(missing_dramas)} drama baru yang siap disedot.")
    
    # 3. Execution
    if missing_dramas:
        for drama in missing_dramas:
            process_single_drama(drama, args.provider, args.dry_run)
            
    print("\n[*] PIPELINE SELESAI.")

if __name__ == '__main__':
    main()
