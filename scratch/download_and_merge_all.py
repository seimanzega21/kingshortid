# -*- coding: utf-8 -*-
import sys
import os
import re
import boto3
import requests
import subprocess
from botocore.config import Config

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# -- R2 Config ---------------------------------------------------------------
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
BUCKET      = 'shortlovers'
API_BASE    = 'https://api.shortlovers.id'

# -- Target folder -----------------------------------------------------------
DEST_ROOT = 'D:/Video Drama/Upload Facebook'

# -- Drama Mappings ----------------------------------------------------------
DRAMA_MAPPINGS = [
    {"target": "Perangkap Cinta yang Salah", "prefix": "netshortv2/perangkap-cinta-yang-salah/"},
    {"target": "Qilin sampah? Kembalikan hadiah!", "prefix": "netshortv2/qilin-sampah-kembalikan-hadiah/"},
    {"target": "Suami yang Mengintip", "prefix": "netshortv2/suami-yang-mengintip/"},
    {"target": "Zona Dewa-Iblis: Penjaga Terakhir", "prefix": "netshortv2/zona-dewa-iblis-penjaga-terakhir/"},
    {"target": "Siapa seret utusan hantu?", "prefix": "netshortv2/siapa-seret-utusan-hantu/"},
    {"target": "Hubungan Berbahaya", "prefix": "netshortv2/hubungan-berbahaya/"},
    {"target": "Tangisan Kehilanganku", "prefix": "netshortv2/tangisan-kehilanganku/"},
    {"target": "(Sulih suara) Main Lemah, Tapi Kuat", "prefix": "netshortv2/sulih-suara-main-lemah-tapi-kuat/", "fallback": "netshortv2/main-lemah-tapi-kuat/"},
    {"target": "Bangkrutkan Suami Selingkuh", "prefix": "netshortv2/bangkrutkan-suami-selingkuh/"},
    {"target": "Mencari Sinar di Lautan", "prefix": "netshortv2/mencari-sinar-di-lautan/"},
    {"target": "Dua Bayi Ajaib", "prefix": "dramas/microdrama/dua-bayi-ajaib/"},
    {"target": "Dikejar Cinta yang Lupa", "prefix": "dramas/microdrama/dikejar-cinta-yang-lupa/"}
]

# -- Initialize boto3 R2 client ----------------------------------------------
r2 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID,
    aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'),
    region_name='auto'
)

def safe_folder_name(title: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '', title).strip()

def fetch_all_dramas() -> list:
    print("[*] Fetching drama list dari API...")
    try:
        r = requests.get(f"{API_BASE}/api/dramas?limit=1000", timeout=30)
        r.raise_for_status()
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', data.get('data', []))
        return dramas
    except Exception as e:
        print(f"    ERROR fetch API: {e}")
        return []

def list_r2_files(prefix: str) -> list:
    files = []
    paginator = r2.get_paginator('list_objects_v2')
    try:
        for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
            for obj in page.get('Contents', []):
                files.append(obj)
    except Exception as e:
        print(f"    ERROR listing R2 for prefix '{prefix}': {e}")
    return files

def download_r2_file(r2_key: str, dest_path: str):
    """Download from R2 to local with progress report."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    head = r2.head_object(Bucket=BUCKET, Key=r2_key)
    total_size = head.get('ContentLength', 0)
    size_mb = total_size / (1024 * 1024)
    fname = os.path.basename(dest_path)
    
    # Check if already fully downloaded
    if os.path.exists(dest_path) and os.path.getsize(dest_path) == total_size:
        return True
        
    print(f"    [DL] {fname} ({size_mb:.2f} MB)... ", end='', flush=True)
    try:
        r2.download_file(Bucket=BUCKET, Key=r2_key, Filename=dest_path)
        print("OK")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def download_url_file(url: str, dest_path: str):
    """Download file from direct HTTP URL (for covers)."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    if os.path.exists(dest_path):
        return True
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            f.write(r.content)
        print(f"    [DL Cover] OK")
        return True
    except Exception as e:
        print(f"    [DL Cover] FAILED: {e}")
        return False

# -- Subtitle Utilities -------------------------------------------------------

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

def shift_vtt_content(content, offset):
    lines = content.split('\n')
    new_lines = []
    pattern = re.compile(r'^(\d{2}:\d{2}(?::\d{2})?\.\d{3})\s*-->\s*(\d{2}:\d{2}(?::\d{2})?\.\d{3})(.*)$')
    for line in lines:
        match = pattern.match(line)
        if match:
            start_str, end_str, rest = match.groups()
            start_sec = time_to_sec(start_str) + offset
            end_sec = time_to_sec(end_str) + offset
            new_line = f"{sec_to_time(start_sec)} --> {sec_to_time(end_sec)}{rest}"
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    return '\n'.join(new_lines)

def get_video_duration(video_path):
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_path}"'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return float(res.stdout.strip())
    except Exception as e:
        print(f"Error getting duration for {video_path}: {e}")
    return 0.0

def build_temp_vtt(dest_folder: str, ep_vtt_files: dict, ep_video_files: dict, start: int, end: int):
    """Build a combined shifted VTT file for the episode chunk. Returns (vtt_filename, has_subtitles)."""
    temp_vtt_filename = f"eps_{start}-{end}_temp.vtt"
    temp_vtt_path = os.path.join(dest_folder, temp_vtt_filename)
    
    merged_lines = ["WEBVTT", ""]
    running_offset = 0.0
    has_subtitles = False

    for ep in range(start, end + 1):
        vtt_file = ep_vtt_files.get(ep)
        video_file = ep_video_files.get(ep)
        
        # 1. Process VTT if exists
        if vtt_file:
            vtt_path = os.path.join(dest_folder, vtt_file)
            if os.path.exists(vtt_path):
                has_subtitles = True
                with open(vtt_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Shift timestamps
                shifted = shift_vtt_content(content, running_offset)
                
                # Strip WEBWTT header and append body
                lines = shifted.split('\n')
                body_started = False
                for line in lines:
                    if body_started:
                        merged_lines.append(line)
                    elif line.strip() == "":
                        continue
                    elif "WEBVTT" in line:
                        continue
                    else:
                        body_started = True
                        merged_lines.append(line)
                merged_lines.append("") # Spacer between episodes
        
        # 2. Add video duration to running offset
        if video_file:
            video_path = os.path.join(dest_folder, video_file)
            if os.path.exists(video_path):
                duration = get_video_duration(video_path)
                running_offset += duration

    if has_subtitles:
        with open(temp_vtt_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(merged_lines))
        return temp_vtt_filename, True
    
    return None, False

# -- Main merge logic --------------------------------------------------------

def merge_episodes_hardsub(dest_folder: str, ep_files: dict, ep_vtt_files: dict, start: int, end: int):
    """Concat video files and burn subtitles permanently using FFmpeg."""
    output_filename = f"eps_{start}-{end}.mp4"
    output_path = os.path.join(dest_folder, output_filename)
    
    if os.path.exists(output_path):
        print(f"    [SKIP MERGE] {output_filename} already exists")
        return True

    # 1. Build the list of files to concat
    concat_list = []
    for ep in range(start, end + 1):
        if ep in ep_files:
            concat_list.append(f"file '{ep_files[ep]}'")
        else:
            print(f"    [WARN] Episode {ep} missing for merge {start}-{end}")
            return False

    if not concat_list:
        return False

    list_path = os.path.join(dest_folder, "list.txt")
    with open(list_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(concat_list) + "\n")

    # 2. Create the temporary shifted VTT subtitle file
    temp_vtt, has_subs = build_temp_vtt(dest_folder, ep_vtt_files, ep_files, start, end)
    
    if has_subs and temp_vtt:
        # Libass defaults to 288 script pixels height for VTT subtitles, which automatically
        # scales to the video resolution. Setting MarginV=95 places the subtitle exactly
        # 1/3 height up from the bottom (288 / 3 = 96). FontSize=16 is optimized for 288p canvas.
        margin_v = 95
        font_size = 16
        
        # Use FFmpeg to concat AND burn subtitles
        cmd = f'ffmpeg -f concat -safe 0 -i list.txt -vf "subtitles={temp_vtt}:force_style=\'Alignment=2,MarginV={margin_v},FontSize={font_size},Outline=1.5,Shadow=0,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1\'" -c:v libx264 -crf 22 -preset veryfast -c:a aac -pix_fmt yuv420p "{output_filename}"'
        print(f"    [HARDSUB MERGE] Concat + render eps {start}-{end} into {output_filename}... ", end='', flush=True)
    else:
        # Fallback to copy concat if no subtitles exist
        cmd = f'ffmpeg -f concat -safe 0 -i list.txt -c copy "{output_filename}"'
        print(f"    [COPY MERGE (NO SUBS)] Concat eps {start}-{end} into {output_filename}... ", end='', flush=True)

    try:
        res = subprocess.run(cmd, cwd=dest_folder, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            print("OK")
            success = True
        else:
            print(f"FAILED (return code {res.returncode})")
            success = False
    except Exception as e:
        print(f"FAILED: {e}")
        success = False

    # Clean up temp files
    if os.path.exists(list_path):
        os.remove(list_path)
    if temp_vtt and os.path.exists(os.path.join(dest_folder, temp_vtt)):
        os.remove(os.path.join(dest_folder, temp_vtt))
        
    return success

def main():
    print("=" * 75)
    print("  DRAMA AUTOMATION: DOWNLOAD & HARDSUB MERGE (BURN-IN)")
    print("=" * 75)
    
    # 1. Fetch API metadata to get covers
    all_dramas = fetch_all_dramas()
    
    # 2. Check if FFmpeg is available
    try:
        subprocess.run('ffmpeg -version', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[*] FFmpeg: AVAILABLE")
    except Exception:
        print("[ERROR] FFmpeg is not found in system PATH. Merging will fail!")
        sys.exit(1)

    for drama_info in DRAMA_MAPPINGS:
        target = drama_info["target"]
        prefix = drama_info["prefix"]
        fallback = drama_info.get("fallback")
        
        print(f"\n{'─'*75}")
        print(f"PROCESSING DRAMA: '{target}'")
        
        # Determine R2 prefix (check fallback if needed)
        files = list_r2_files(prefix)
        if not files and fallback:
            print(f"  -> Primary prefix '{prefix}' is empty. Trying fallback '{fallback}'...")
            prefix = fallback
            files = list_r2_files(prefix)
            
        if not files:
            print(f"  [ERROR] No files found in R2 for '{target}' under prefixes.")
            continue
            
        print(f"  R2 Prefix: '{prefix}'")
        print(f"  Total files in prefix: {len(files)}")
        
        # Create helper lookup set of all keys in this prefix
        r2_keys_set = {f['Key'] for f in files}
        
        # 3. Filter for MP4 video files and group by episode number
        video_files = [f for f in files if f['Key'].lower().endswith('.mp4')]
        ep_groups = {}
        for f in video_files:
            key_name = os.path.basename(f['Key'])
            match = re.search(r'ep(\d+)', key_name, re.IGNORECASE)
            if match:
                ep_num = int(match.group(1))
                if ep_num not in ep_groups:
                    ep_groups[ep_num] = []
                ep_groups[ep_num].append(f)
                
        if not ep_groups:
            print("  [ERROR] No episode files found matching 'ep(\\d+)' pattern.")
            continue
            
        print(f"  Detected {len(ep_groups)} unique episodes.")
        
        # Create output folder
        folder_name = safe_folder_name(target)
        dest_folder = os.path.join(DEST_ROOT, folder_name)
        os.makedirs(dest_folder, exist_ok=True)
        
        # 4. Download cover image if available from API
        api_drama = next((d for d in all_dramas if normalize_title(d.get('title', '')) == normalize_title(target)), None)
        if api_drama and api_drama.get('cover'):
            cover_url = api_drama['cover']
            ext = os.path.splitext(cover_url.split('?')[0])[1] or '.jpg'
            cover_dest = os.path.join(dest_folder, f"cover{ext}")
            download_url_file(cover_url, cover_dest)
            
        # 5. Select largest video file and download, then download VTT
        downloaded_eps = {}
        downloaded_vtts = {}
        
        for ep_num in sorted(ep_groups.keys()):
            candidates = ep_groups[ep_num]
            best_video = max(candidates, key=lambda x: x.get('Size', 0))
            
            # Save local video as ep_001.mp4
            local_video_name = f"ep_{ep_num:03d}.mp4"
            local_video_path = os.path.join(dest_folder, local_video_name)
            
            ok_video = download_r2_file(best_video['Key'], local_video_path)
            if ok_video:
                downloaded_eps[ep_num] = local_video_name
                
            # Find matching subtitle in R2 keys (replace .mp4 with .vtt)
            vtt_key = best_video['Key'].replace('.mp4', '.vtt')
            if vtt_key not in r2_keys_set:
                ep_base_match = re.search(r'ep\d+', best_video['Key'], re.IGNORECASE)
                if ep_base_match:
                    standard_vtt_name = ep_base_match.group(0).lower() + '.vtt'
                    vtt_key = prefix + standard_vtt_name
            
            if vtt_key in r2_keys_set:
                local_vtt_name = f"ep_{ep_num:03d}.vtt"
                local_vtt_path = os.path.join(dest_folder, local_vtt_name)
                ok_vtt = download_r2_file(vtt_key, local_vtt_path)
                if ok_vtt:
                    downloaded_vtts[ep_num] = local_vtt_name
                
        # 6. Merge downloaded episodes per 5 with hardsubs
        print(f"  Merging episodes & burning subtitles per 5 for '{target}'...")
        all_ep_numbers = sorted(downloaded_eps.keys())
        if not all_ep_numbers:
            print("  [WARN] No episodes downloaded. Skipping merge.")
            continue
            
        max_ep = all_ep_numbers[-1]
        
        chunk_start = 1
        while chunk_start <= max_ep:
            chunk_end = chunk_start + 4
            chunk_eps = [ep for ep in range(chunk_start, chunk_end + 1) if ep in all_ep_numbers]
            if chunk_eps:
                merge_episodes_hardsub(dest_folder, downloaded_eps, downloaded_vtts, chunk_start, chunk_end)
            chunk_start += 5

    print("\n" + "=" * 75)
    print("  ALL DRAMAS DOWNLOADED & HARDSUB MERGED SUCCESSFULLY!")
    print("  Check files under:", DEST_ROOT)
    print("=" * 75)

def normalize_title(title: str) -> str:
    title = re.sub(r'\([^)]*\)', '', title)
    title = re.sub(r'[^a-zA-Z0-9\s]', ' ', title)
    return re.sub(r'\s+', ' ', title.strip().lower())

if __name__ == "__main__":
    main()
