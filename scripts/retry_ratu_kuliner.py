"""
Retry episode yang gagal untuk drama '[Versi Dub] Ratu Kuliner: Resep Balas Dendam'
Hanya memproses episode yang belum ada di DB, skip yang sudah ada.
"""
import requests, boto3, subprocess, time, urllib3, re
from pathlib import Path
from botocore.config import Config
import tempfile

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── CONFIG ────────────────────────────────────────────────────────────────────
API_BASE   = 'https://api.shortlovers.id/api'
ADMIN_KEY  = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR  = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

DB_DRAMA_ID  = 'cgksop53bcb1cuhs0wpu5tv2'   # ID di database kita
VID_DRAMA_ID = '6a0572b216e8f854a6012561'    # ID di Vidrama
SLUG         = 'versi-dub-ratu-kuliner-resep-balas-dendam'
PREFIX       = f'netshortv2/{SLUG}'

TEMP_DIR = Path(tempfile.gettempdir()) / 'ratu_kuliner_retry'
TEMP_DIR.mkdir(exist_ok=True)

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

def r2_upload(r2, local_path, key):
    r2.upload_file(str(local_path), R2_BUCKET, key,
                   ExtraArgs={'ContentType': 'video/mp4'},
                   Config=boto3.s3.transfer.TransferConfig(
                       multipart_threshold=30*1024*1024,
                       multipart_chunksize=10*1024*1024))
    return f'{R2_PUBLIC}/{key}'

def srt_to_vtt(content):
    if content.strip().startswith('WEBVTT'):
        return content
    lines = content.replace('\r\n', '\n').split('\n')
    vtt = ['WEBVTT\n']
    ts = re.compile(r'(\d{2}:\d{2}:\d{2}),(\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}),(\d{3})')
    for line in lines:
        m = ts.search(line)
        vtt.append(ts.sub(r'\1.\2 --> \3.\4', line) if m else line)
    return '\n'.join(vtt)

def encode_720_and_540(inp, out_720, out_540):
    r1 = subprocess.run([
        'ffmpeg', '-y', '-i', str(inp),
        '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
        '-maxrate', '1500k', '-bufsize', '3000k',
        '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
        '-loglevel', 'error', str(out_720)
    ], timeout=600)
    if r1.returncode != 0:
        return False
    r2 = subprocess.run([
        'ffmpeg', '-y', '-i', str(out_720),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart',
        '-loglevel', 'error', str(out_540)
    ], timeout=600)
    return r2.returncode == 0

def api_upsert_episode(ep_no, url_720, url_540=None, sub_url=None):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720,
        'isActive': True,
        'dramaId': DB_DRAMA_ID,
    }
    if url_540:
        payload['videoUrl540p'] = url_540
    r = requests.post(f'{API_BASE}/admin/dramas/{DB_DRAMA_ID}/episodes',
                      headers=ADMIN_HDR, json=payload, timeout=20)
    if not r.ok:
        print(f'      [WARN] Episode upsert failed: {r.status_code}')
        return None
    ep_id = r.json().get('id')
    if ep_id and sub_url:
        requests.post(f'{API_BASE}/episodes/{ep_id}/subtitles', headers=ADMIN_HDR,
                      json={'language': 'indonesia', 'label': 'Indonesia',
                            'url': sub_url, 'isDefault': True}, timeout=10)
    return ep_id

def main():
    r2 = get_r2()

    print(f'=== Retry Episode Gagal: [Versi Dub] Ratu Kuliner: Resep Balas Dendam ===')
    print(f'DB ID : {DB_DRAMA_ID}')
    print(f'Vid ID: {VID_DRAMA_ID}')
    print()

    # Ambil daftar semua episode dari Vidrama
    meta_url = f'https://vidrama.asia/api/reelshort/detail?id={VID_DRAMA_ID}'
    meta_resp = requests.get(meta_url, headers=WEB_HDRS, timeout=20, verify=False)
    if not meta_resp.ok:
        print(f'ERROR: Tidak bisa ambil metadata: {meta_resp.status_code}')
        return

    meta = meta_resp.json()
    chapters = meta.get('chapters', [])
    total_source = len(chapters)
    print(f'Total episode di sumber: {total_source}')

    # Cari episode yang missing dengan mengecek R2
    print('Mengecek episode di R2...')
    source_eps = [ch.get('index') for ch in chapters if ch.get('index') is not None]
    source_eps.sort()
    
    missing = []
    for ep_no in source_eps:
        k720 = f'{PREFIX}/ep{ep_no:03d}.mp4'
        if not r2_exists(r2, k720):
            missing.append(ep_no)
            
    print(f'Episode missing di R2 ({len(missing)}): {missing}')
    print()

    if not missing:
        print(' Semua episode sudah lengkap di R2!')
        return

    # Retry episode yang missing
    success = 0
    failed = 0
    still_locked = []

    for ep_no in missing:
        k720 = f'{PREFIX}/ep{ep_no:03d}.mp4'
        k540 = f'{PREFIX}/ep{ep_no:03d}_540p.mp4'
        ksub = f'{PREFIX}/ep{ep_no:03d}.vtt'

        print(f'  ep{ep_no:03d}: Mencoba download...', end='', flush=True)

        # Coba semua lang param
        vurl = None
        subtitles = []
        for lang_param in ['&lang=id', '', '&lang=in']:
            if vurl:
                break
            for attempt in range(3):
                ep_url = f'https://vidrama.asia/api/reelshort/video?bookId={VID_DRAMA_ID}&episode={ep_no}{lang_param}'
                try:
                    er = requests.get(ep_url, headers=WEB_HDRS, timeout=15, verify=False)
                    if er.ok:
                        ep_data = er.json()
                        if ep_data.get('success') and (ep_data.get('rawVideoUrl') or ep_data.get('videoUrl')):
                            vurl = ep_data.get('rawVideoUrl') or ep_data.get('videoUrl')
                            subtitles = ep_data.get('subtitles', [])
                            break
                    time.sleep(3)
                except:
                    time.sleep(3)

        if not vurl:
            print(' LOCKED/TIDAK TERSEDIA ')
            failed += 1
            still_locked.append(ep_no)
            continue

        if vurl.startswith('/api/'):
            vurl = f'https://vidrama.asia{vurl}'

        # Download & transcode
        raw_path = TEMP_DIR / f'ratu_raw_{ep_no}.mp4'
        o720_path = TEMP_DIR / f'ratu_720_{ep_no}.mp4'
        o540_path = TEMP_DIR / f'ratu_540_{ep_no}.mp4'

        headers_str = f"Referer: https://vidrama.asia/\r\nUser-Agent: {WEB_HDRS['User-Agent']}\r\n"
        try:
            res = subprocess.run([
                'ffmpeg', '-y', '-headers', headers_str,
                '-i', vurl, '-c', 'copy', '-loglevel', 'error', str(raw_path)
            ], timeout=300)

            if res.returncode == 0 and raw_path.exists() and raw_path.stat().st_size > 50*1024:
                if encode_720_and_540(raw_path, o720_path, o540_path):
                    u720 = r2_upload(r2, o720_path, k720)
                    u540 = r2_upload(r2, o540_path, k540)

                    # Handle subtitle
                    sub_url = None
                    for s in subtitles:
                        lang = s.get('lang', s.get('language', '')).lower()
                        if lang in ['id', 'id_id', 'in', 'in_id', 'indonesia']:
                            try:
                                sr = requests.get(s.get('url'), timeout=10, verify=False)
                                if sr.ok:
                                    vtt = srt_to_vtt(sr.content.decode('utf-8', errors='ignore'))
                                    r2.put_object(Bucket=R2_BUCKET, Key=ksub,
                                                  Body=vtt.encode('utf-8'), ContentType='text/vtt')
                                    sub_url = f'{R2_PUBLIC}/{ksub}'
                            except:
                                pass
                            break

                    api_upsert_episode(ep_no, u720, u540, sub_url)
                    print(' SUCCESS')
                    success += 1
                else:
                    print(' ERROR (transcode gagal)')
                    failed += 1
                    still_locked.append(ep_no)
            else:
                print(' ERROR (download gagal)')
                failed += 1
                still_locked.append(ep_no)
        except Exception as e:
            print(f' ERROR ({e})')
            failed += 1
            still_locked.append(ep_no)
        finally:
            for p in [raw_path, o720_path, o540_path]:
                if p.exists():
                    p.unlink()

        time.sleep(1)

    print()
    print(f'=== SELESAI ===')
    print(f'Berhasil dipulihkan : {success} episode')
    print(f'Tetap gagal         : {failed} episode')
    if still_locked:
        print(f'Masih locked/tidak tersedia: {still_locked}')

if __name__ == '__main__':
    main()
