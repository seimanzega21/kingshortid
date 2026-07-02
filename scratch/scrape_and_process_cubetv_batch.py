# -*- coding: utf-8 -*-
"""
Orchestration script for batch scraping, transcoding, DB registering, and Facebook processing
of multiple dramas from cubetv provider.
"""
import os
import sys
import re
import time
import requests
import boto3
import subprocess
import argparse
import urllib3
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings()
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─── CONFIGURATION ──────────────────────────────────────────────────────────
DRAMA_LIST = [
    {"upstream_id": "m0WBLa"}, # Siswa Kejuruan, Terbaik Dunia (52 episodes)
    {"upstream_id": "QZpz60"}  # Bertani Menjinakkan Dewa Dingin (65 episodes)
]

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET = 'shortlovers'
R2_PUBLIC = 'https://stream.shortlovers.id'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

# Directories
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = WORKSPACE_DIR / 'temp_cubetv_batch'
TEMP_DIR.mkdir(exist_ok=True)
LOG_FILE = WORKSPACE_DIR / 'scratch' / 'scrape_cubetv_batch.log'
DEST_ROOT = 'D:/Video Drama/Facebook2'

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(full_msg + '\n')

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def make_slug(title):
    s = title.strip().lower()
    s = s.replace("(dubbing)", "")
    s = s.replace("(sulih suara)", "")
    s = s.replace("(", "").replace(")", "")
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s-]+', '-', s)
    return s.strip('-')

def srt_to_vtt(srt_text):
    if srt_text.strip().startswith('WEBVTT'):
        return srt_text
    lines = srt_text.splitlines()
    vtt_lines = ['WEBVTT', '']
    timestamp_re = re.compile(r'(\d{2}:\d{2}:\d{2}),(\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}),(\d{3})')
    for line in lines:
        match = timestamp_re.search(line)
        if match:
            formatted_line = line.replace(',', '.')
            vtt_lines.append(formatted_line)
        else:
            vtt_lines.append(line)
    return '\n'.join(vtt_lines)

def vtt_to_srt(vtt_text):
    # Convert VTT back to SRT
    lines = vtt_text.splitlines()
    srt_lines = []
    timestamp_re = re.compile(r'(\d{2}:\d{2}:\d{2})\.(\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2})\.(\d{3})')
    index = 1
    i = 0
    # Skip WEBVTT header lines
    while i < len(lines) and (lines[i].strip().startswith('WEBVTT') or lines[i].strip() == ''):
        i += 1
    
    while i < len(lines):
        line = lines[i].strip()
        match = timestamp_re.search(line)
        if match:
            srt_lines.append(str(index))
            formatted_line = line.replace('.', ',')
            srt_lines.append(formatted_line)
            index += 1
            i += 1
            # Add dialogue lines
            while i < len(lines) and lines[i].strip() != '':
                srt_lines.append(lines[i].strip())
                i += 1
            srt_lines.append('') # Empty line separator
        else:
            i += 1
    return '\n'.join(srt_lines)

def get_db_drama_by_title(title):
    r = requests.get(f"{API_BASE}/admin/dramas?limit=5000", headers=ADMIN_HDR, timeout=20)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', data.get('data', []))
        for d in dramas:
            if d.get('title', '').strip().lower() == title.strip().lower():
                return d.get('id')
        target_slug = make_slug(title)
        for d in dramas:
            if make_slug(d.get('title', '')) == target_slug:
                return d.get('id')
    return None

def register_drama_api(title, description, cover_url, total_eps):
    payload = {
        'title': title,
        'description': description,
        'cover': cover_url,
        'genres': ['Drama', 'Emosional'],
        'totalEpisodes': total_eps,
        'status': 'completed',
        'country': 'China',
        'language': 'Indonesia',
        'isActive': False,  # Pending
        'isVip': False
    }
    r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        return r.json().get('id')
    log(f"  [ERROR] Failed to register drama. Status: {r.status_code}, Body: {r.text[:200]}")
    return None

def get_registered_episodes(drama_db_id):
    r = requests.get(f"{API_BASE}/dramas/{drama_db_id}/episodes?includeInactive=true", headers=ADMIN_HDR, timeout=15)
    if r.ok:
        eps = r.json()
        ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
        return {e.get('episodeNumber'): (e.get('id'), e.get('videoUrl'), e.get('videoUrl540p')) for e in ep_list if e.get('episodeNumber')}
    return {}

def download_file(url, local_path):
    with requests.get(url, headers=HEADERS, stream=True, timeout=60, verify=False) as r:
        if r.status_code == 200:
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=2*1024*1024):
                    if chunk:
                        f.write(chunk)
            return True
    return False

def download_m3u8_stream(m3u8_url, local_path):
    headers_str = f"Referer: https://vidrama.asia/\r\nUser-Agent: {HEADERS['User-Agent']}\r\n"
    cmd = [
        'ffmpeg', '-y',
        '-headers', headers_str,
        '-i', m3u8_url,
        '-c:v', 'libx264', '-crf', '26',
        '-preset', 'fast',
        '-maxrate', '1500k', '-bufsize', '3000k',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(local_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.returncode == 0

def downscale_to_540p(input_path, output_path):
    cmd = [
        'ffmpeg', '-y', '-i', str(input_path),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28',
        '-preset', 'fast',
        '-maxrate', '800k', '-bufsize', '1600k',
        '-c:a', 'copy',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(output_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.returncode == 0

def r2_upload_file(r2, local_path, key, content_type='video/mp4'):
    r2.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={
        'ContentType': content_type,
        'CacheControl': 'public, max-age=31536000'
    })
    return f"{R2_PUBLIC}/{key}"

def register_episode_db(drama_db_id, ep_no, url_720, url_540):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720,
        'videoUrl540p': url_540,
        'isVip': False,
        'coinPrice': 0,
        'isActive': True
    }
    r = requests.post(f"{API_BASE}/admin/dramas/{drama_db_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
    if r.ok:
        return r.json().get('id')
    return None

def register_subtitles_db(episode_db_id, r2_sub_url):
    payload = {
        'language': 'id',
        'label': 'Bahasa Indonesia',
        'url': r2_sub_url,
        'isDefault': True
    }
    r = requests.post(f"{API_BASE}/episodes/{episode_db_id}/subtitles", headers=ADMIN_HDR, json=payload, timeout=15)
    return r.ok

# ─── FACEBOOK SUBTITLE & MERGING UTILITIES ──────────────────────────────────
def time_to_sec(t_str):
    parts = t_str.split(':')
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h = 0
        m, s = parts
    else:
        return 0.0
    return int(h) * 3600 + int(m) * 60 + float(s)

def sec_to_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"

def get_video_duration(video_path):
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_path}"'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return float(res.stdout.strip())
    except Exception as e:
        log(f"Error getting duration for {video_path}: {e}")
    return 0.0

def get_video_height(video_path):
    cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "{video_path}"'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return int(res.stdout.strip())
    except Exception as e:
        log(f"Error getting height for {video_path}: {e}")
    return 1280

def get_video_width(video_path):
    cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=width -of default=noprint_wrappers=1:nokey=1 "{video_path}"'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return int(res.stdout.strip())
    except Exception as e:
        log(f"Error getting width for {video_path}: {e}")
    return 720

def sec_to_ass_time(sec):
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    cs = int(round((s - int(s)) * 100))
    if cs >= 100:
        s += 1
        cs -= 100
    return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"

def build_temp_ass(dest_folder, ep_vtt_files, ep_video_files, start, end, width, height, font_size=40):
    temp_ass_filename = f"eps_{start}-{end}_temp.ass"
    temp_ass_path = os.path.join(dest_folder, temp_ass_filename)
    
    margin_v = height // 4
    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    dialogues = []
    running_offset = 0.0
    has_subtitles = False
    timestamp_pattern = re.compile(r'^(\d{2}:\d{2}(?::\d{2})?\.\d{3})\s*-->\s*(\d{2}:\d{2}(?::\d{2})?\.\d{3})')

    for ep in range(start, end + 1):
        vtt_file = ep_vtt_files.get(ep)
        video_file = ep_video_files.get(ep)
        
        if vtt_file:
            vtt_path = os.path.join(dest_folder, vtt_file)
            if os.path.exists(vtt_path):
                has_subtitles = True
                with open(vtt_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                lines = content.split('\n')
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    match = timestamp_pattern.match(line)
                    if match:
                        start_str, end_str = match.groups()
                        start_sec = time_to_sec(start_str) + running_offset
                        end_sec = time_to_sec(end_str) + running_offset
                        
                        text_lines = []
                        i += 1
                        while i < len(lines) and lines[i].strip() != "":
                            text_lines.append(lines[i].strip())
                            i += 1
                        
                        text = "\\N".join(text_lines)
                        text = re.sub(r'<[^>]+>', '', text)
                        
                        start_ass = sec_to_ass_time(start_sec)
                        end_ass = sec_to_ass_time(end_sec)
                        dialogues.append(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}")
                    else:
                        i += 1
        
        if video_file:
            video_path = os.path.join(dest_folder, video_file)
            duration = get_video_duration(video_path)
            running_offset += duration

    if has_subtitles:
        with open(temp_ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_header)
            f.write("\n".join(dialogues) + "\n")
        return temp_ass_filename, True
    
    return None, False

def merge_episodes_hardsub(dest_folder, ep_files, ep_vtt_files, start, end):
    output_filename = f"eps_{start}-{end}.mp4"
    output_path = os.path.join(dest_folder, output_filename)
    
    if os.path.exists(output_path):
        log(f"    [SKIP MERGE] {output_filename} already exists")
        return True

    concat_list = []
    first_video_path = None
    for ep in range(start, end + 1):
        if ep in ep_files:
            concat_list.append(f"file '{ep_files[ep]}'")
            if not first_video_path:
                first_video_path = os.path.join(dest_folder, ep_files[ep])
        else:
            log(f"    [WARN] Episode {ep} missing for merge {start}-{end}")
            return False

    if not concat_list:
        return False

    list_path = os.path.join(dest_folder, "list.txt")
    with open(list_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(concat_list) + "\n")

    height = get_video_height(first_video_path)
    width = get_video_width(first_video_path)

    temp_ass, has_subs = build_temp_ass(dest_folder, ep_vtt_files, ep_files, start, end, width, height, font_size=40)
    
    if has_subs and temp_ass:
        cmd = f'ffmpeg -y -f concat -safe 0 -i list.txt -vf "subtitles={temp_ass},setpts=0.95238*PTS" -af "atempo=1.05" -c:v libx264 -crf 22 -preset veryfast -c:a aac -pix_fmt yuv420p "{output_filename}"'
        log(f"    [HARDSUB CONCAT + SPEEDUP] Concat eps {start}-{end} into {output_filename} (MarginV={height // 4}, FontSize=40, Speed=1.05)... ")
    else:
        cmd = f'ffmpeg -y -f concat -safe 0 -i list.txt -vf "setpts=0.95238*PTS" -af "atempo=1.05" -c:v libx264 -crf 22 -preset veryfast -c:a aac -pix_fmt yuv420p "{output_filename}"'
        log(f"    [CONCAT + SPEEDUP (NO SUBS)] Concat eps {start}-{end} into {output_filename} (Speed=1.05)... ")

    try:
        res = subprocess.run(cmd, cwd=dest_folder, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            log("      [OK] Merged successfully")
            success = True
        else:
            log(f"      [ERROR] Merge failed (return code {res.returncode})")
            success = False
    except Exception as e:
        log(f"      [ERROR] Merge failed: {e}")
        success = False

    # Cleanup temp list/ass files
    if os.path.exists(list_path):
        os.remove(list_path)
    if temp_ass and os.path.exists(os.path.join(dest_folder, temp_ass)):
        os.remove(os.path.join(dest_folder, temp_ass))
        
    return success

# ─── MAIN BATCH PIPELINE ────────────────────────────────────────────────────
def main():
    # Clear log file
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("--- CUBETV BATCH SCRAPER PIPELINE LOG STARTED ---\n")

    log("=" * 70)
    log("STARTING CUBETV BATCH INGESTION AND PROCESSING")
    log("=" * 70)

    r2 = get_r2()

    for item in DRAMA_LIST:
        upstream_id = item["upstream_id"]
        log(f"\n\n{'='*30} PROCESSING UPSTREAM ID: {upstream_id} {'='*30}")
        
        # 1. Fetch metadata & episode list
        detail_url = f"https://vidrama.asia/api/proxy-cubetv/detail/{upstream_id}?lang=id"
        episodes_url = f"https://vidrama.asia/api/proxy-cubetv/episodes/{upstream_id}?lang=id"

        try:
            r_det = requests.get(detail_url, headers=HEADERS, verify=False, timeout=20)
            r_eps = requests.get(episodes_url, headers=HEADERS, verify=False, timeout=20)
            if not r_det.ok or not r_eps.ok:
                log(f"[ERROR] Failed to fetch metadata or episodes from upstream API. Statuses: {r_det.status_code}, {r_eps.status_code}")
                continue
        except Exception as e:
            log(f"[ERROR] Connection to vidrama failed: {e}")
            continue

        det_data = r_det.json().get('data', {})
        eps_data = r_eps.json()
        eps_list = eps_data if isinstance(eps_data, list) else eps_data.get('rows', eps_data.get('data', []))

        title = det_data.get('videoName', '').strip()
        description = det_data.get('summary', '').strip()
        cover_raw = det_data.get('cover', '')
        total_eps = len(eps_list)

        if not title:
            log("[ERROR] Drama title is empty, skipping.")
            continue

        log(f"Drama Title: {title}")
        log(f"Total Episodes in list: {total_eps}")
        log(f"Cover URL: {cover_raw}")

        # Check if episodes list is empty (e.g. QZpz60)
        if total_eps == 0:
            log(f"[WARN] Episode list is empty for upstream ID: {upstream_id}. Provider has not uploaded video files yet. Skipping this drama.")
            continue

        # Set up final folders
        folder_name = re.sub(r'[<>:"/\\|?*]', '', title).strip()
        local_dest_dir = Path(DEST_ROOT) / folder_name
        local_dest_dir.mkdir(parents=True, exist_ok=True)
        log(f"Local output folder: {local_dest_dir}")

        # 2. Database Drama Registration/Lookup
        log("Checking database for drama...")
        drama_db_id = get_db_drama_by_title(title)
        
        if drama_db_id:
            log(f"[OK] Drama already registered in DB. ID: {drama_db_id}")
        else:
            log("Uploading cover image to R2...")
            cover_r2_url = cover_raw
            if cover_raw:
                try:
                    cov_r = requests.get(cover_raw, timeout=20, verify=False)
                    if cov_r.ok:
                        cover_key = f"dramas/{make_slug(title)}/cover.jpg"
                        r2.put_object(Bucket=R2_BUCKET, Key=cover_key, Body=cov_r.content, ContentType='image/jpeg')
                        cover_r2_url = f"{R2_PUBLIC}/{cover_key}"
                        log(f"  [OK] Cover uploaded: {cover_r2_url}")
                except Exception as e:
                    log(f"  [WARN] Cover upload failed: {e}")
            
            log("Registering drama in DB (status=Pending)...")
            drama_db_id = register_drama_api(title, description, cover_r2_url, total_eps)
            if not drama_db_id:
                log("[ERROR] Drama registration failed. Skipping.")
                continue
            log(f"[OK] Registered drama DB ID: {drama_db_id}")

        # 3. Process Episodes
        registered_eps = get_registered_episodes(drama_db_id)
        log(f"Currently registered episodes in DB: {sorted(list(registered_eps.keys()))}")

        downloaded_video_names = {}
        downloaded_vtt_names = {}

        for ep in eps_list:
            ep_no = ep.get('episodeNumber')
            ep_id = ep.get('episodeid')
            subs_list = ep.get('subtitles', [])
            video_urls = ep.get('videoUrls', [])

            log(f"\n--- Episode {ep_no} ---")

            local_mp4_name = f"ep_{ep_no:03d}.mp4"
            local_srt_name = f"ep_{ep_no:03d}.srt"
            local_vtt_name = f"ep_{ep_no:03d}.vtt"

            local_mp4_path = local_dest_dir / local_mp4_name
            local_srt_path = local_dest_dir / local_srt_name
            local_vtt_path = local_dest_dir / local_vtt_name

            # Find Indonesian subtitle url
            sub_url = None
            for s in subs_list:
                if s.get('lang') == 'id' and s.get('url'):
                    sub_url = s['url']
                    break

            # A. If already registered
            if ep_no in registered_eps:
                log("  Already registered in DB.")
                db_ep_id, db_url_720, db_url_540 = registered_eps[ep_no]
                
                # Check local files and download from R2 if missing
                if not local_mp4_path.exists():
                    log(f"  Downloading 720p from R2: {db_url_720}...")
                    if not download_file(db_url_720, local_mp4_path):
                        log("    [ERROR] Download from R2 failed")
                
                # Download Indonesian subtitle VTT from R2 to local VTT and convert to SRT
                vtt_r2_url = f"{R2_PUBLIC}/dramas/{make_slug(title)}/ep{ep_no:03d}_id.vtt"
                if not local_vtt_path.exists() or not local_srt_path.exists():
                    log("  Downloading and converting subtitle from R2...")
                    try:
                        sub_r = requests.get(vtt_r2_url, timeout=15, verify=False)
                        if sub_r.ok:
                            with open(local_vtt_path, 'w', encoding='utf-8') as f:
                                f.write(sub_r.text)
                            
                            # Convert to SRT
                            srt_text = vtt_to_srt(sub_r.text)
                            with open(local_srt_path, 'w', encoding='utf-8') as f:
                                f.write(srt_text)
                    except Exception as e:
                        if sub_url:
                            log("    R2 subtitle retrieval failed. Fetching from upstream...")
                            try:
                                sub_r = requests.get(sub_url, headers=HEADERS, timeout=15, verify=False)
                                if sub_r.ok:
                                    with open(local_srt_path, 'wb') as f:
                                        f.write(sub_r.content)
                                    vtt_text = srt_to_vtt(sub_r.text)
                                    with open(local_vtt_path, 'w', encoding='utf-8') as f:
                                        f.write(vtt_text)
                            except Exception as ex:
                                log(f"    [WARN] Upstream subtitle download failed: {ex}")

                downloaded_video_names[ep_no] = local_mp4_name
                if local_vtt_path.exists():
                    downloaded_vtt_names[ep_no] = local_vtt_name
                continue

            # B. If not registered, perform download, transcode, upload, and registration
            if not video_urls:
                log("  [ERROR] No video stream URL found. Skipping.")
                continue

            m3u8_url = video_urls[0]['url']
            out_720_temp = TEMP_DIR / f"ep{ep_no:03d}_720p.mp4"
            out_540_temp = TEMP_DIR / f"ep{ep_no:03d}_540p.mp4"

            try:
                # 1. Download and transcode 720p faststart
                log("  Downloading and transcoding 720p...")
                t0 = time.time()
                if not download_m3u8_stream(m3u8_url, out_720_temp):
                    log("    [ERROR] Transcoding 720p failed")
                    continue
                log(f"    [OK] 720p done: {out_720_temp.stat().st_size / 1024 / 1024:.1f}MB (took {time.time()-t0:.1f}s)")

                # 2. Downscale to 540p faststart
                log("  Downscaling to 540p...")
                t0 = time.time()
                if not downscale_to_540p(out_720_temp, out_540_temp):
                    log("    [ERROR] Downscaling failed")
                    continue
                log(f"    [OK] 540p done: {out_540_temp.stat().st_size / 1024 / 1024:.1f}MB (took {time.time()-t0:.1f}s)")

                # 3. Upload to R2
                slug_name = make_slug(title)
                key_720 = f"dramas/{slug_name}/ep{ep_no:03d}_720p.mp4"
                key_540 = f"dramas/{slug_name}/ep{ep_no:03d}_540p.mp4"
                
                r2_url_720 = r2_upload_file(r2, out_720_temp, key_720)
                r2_url_540 = r2_upload_file(r2, out_540_temp, key_540)
                log("    [OK] Uploaded video files")

                # 4. Handle Subtitle
                r2_sub_url = None
                if sub_url:
                    log("  Downloading and uploading subtitle...")
                    try:
                        sub_r = requests.get(sub_url, headers=HEADERS, timeout=15, verify=False)
                        if sub_r.ok:
                            with open(local_srt_path, 'wb') as f:
                                f.write(sub_r.content)
                            
                            vtt_text = srt_to_vtt(sub_r.text)
                            with open(local_vtt_path, 'w', encoding='utf-8') as f:
                                f.write(vtt_text)
                            
                            sub_key = f"dramas/{slug_name}/ep{ep_no:03d}_id.vtt"
                            r2.put_object(Bucket=R2_BUCKET, Key=sub_key, Body=vtt_text.encode('utf-8'), ContentType='text/vtt')
                            r2_sub_url = f"{R2_PUBLIC}/{sub_key}"
                            log(f"    [OK] Subtitle uploaded: {r2_sub_url}")
                    except Exception as e:
                        log(f"    [WARN] Subtitle download/upload failed: {e}")

                # 5. DB Ingestion
                log("  Registering episode in DB...")
                ep_db_id = register_episode_db(drama_db_id, ep_no, r2_url_720, r2_url_540)
                if ep_db_id:
                    log("    [OK] Episode registered in DB")
                    if r2_sub_url:
                        register_subtitles_db(ep_db_id, r2_sub_url)
                        log("    [OK] Subtitle registered in DB")
                    
                    import shutil
                    shutil.copy(str(out_720_temp), str(local_mp4_path))
                    log(f"    [OK] Saved locally to: {local_mp4_path}")

                    downloaded_video_names[ep_no] = local_mp4_name
                    if local_vtt_path.exists():
                        downloaded_vtt_names[ep_no] = local_vtt_name
                else:
                    log("    [ERROR] Episode DB registration failed")

            except Exception as e:
                log(f"  [ERROR] Error processing episode {ep_no}: {e}")
            finally:
                for p in [out_720_temp, out_540_temp]:
                    if p.exists():
                        try:
                            p.unlink()
                        except: pass
            
            time.sleep(1.0)

        # 4. Facebook Hardsub & Merge packages per 5 episodes
        log("\n" + "=" * 65)
        log(f"STARTING FACEBOOK MERGE PACKAGES (PER 5 EPISODES) FOR '{title}'...")
        log("=" * 65)

        max_ep = total_eps
        chunk_start = 1
        merge_success = 0
        merge_failed = 0

        while chunk_start <= max_ep:
            chunk_end = min(chunk_start + 4, max_ep)
            chunk_eps = [ep for ep in range(chunk_start, chunk_end + 1) if ep in downloaded_video_names]
            
            if len(chunk_eps) > 0:
                if merge_episodes_hardsub(str(local_dest_dir), downloaded_video_names, downloaded_vtt_names, chunk_start, chunk_end):
                    merge_success += 1
                else:
                    merge_failed += 1
            chunk_start += 5

        log("\n" + "=" * 65)
        log(f"FINISHED PROCESSING DRAMA '{title}'!")
        log(f"Total processed episodes: {len(downloaded_video_names)} / {total_eps}")
        log(f"Merged Facebook packages succeeded: {merge_success}")
        if merge_failed > 0:
            log(f"Merged Facebook packages failed: {merge_failed}")
        log(f"All final video files are saved at: {local_dest_dir}")
        log("=" * 65)

    log("\n\n" + "=" * 70)
    log("BATCH PIPELINE PROCESSING COMPLETED SUCCESSFULLY!")
    log("=" * 70)

if __name__ == '__main__':
    main()
