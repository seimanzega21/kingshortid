# -*- coding: utf-8 -*-
"""
Drama Automation: Download R2, Hardsub (MarginV = height/4, FontSize = 40),
Speed Up 1.05x, and Merge per 5 Episodes to D:/Video Drama/Facebook2/
"""
import sys
import os
import re
import boto3
import requests
import subprocess
import argparse
from botocore.config import Config

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# -- Config ------------------------------------------------------------------
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
BUCKET      = 'shortlovers'
DEST_ROOT   = 'D:/Video Drama/Facebook2'

DRAMA_LIST = [
    {"title": "Aku Adalah Putri dari Dunia Terlarang", "slug": "aku-adalah-putri-dari-dunia-terlarang"},
    {"title": "Tidur Sekejap, Terbangun Sepuluh Tahun Kemudian", "slug": "tidur-sekejap-terbangun-sepuluh-tahun-kemudian"},
    {"title": "Sistem Kultivasi Pengubah Takdir", "slug": "sistem-kultivasi-pengubah-takdir"},
    {"title": "Ratu Mafia yang Menjinakkan Hati Pria Desa", "slug": "ratu-mafia-yang-menjinakkan-hati-pria-desa"},
    {"title": "Dewa yang turun dari gunung", "slug": "dewa-yang-turun-dari-gunung"},
    {"title": "(Sulih Suara) Bunga violet di balik pakaian", "slug": "bunga-violet-di-balik-pakaian"},
    {"title": "(Sulih Suara) Dua Bayi Kecil Satukan Ayah Ibu", "slug": "dua-bayi-kecil-satukan-ayah-ibu"},
    {"title": "(Sulih Suara) Putri Sejati Sang Mahaguru", "slug": "putri-sejati-sang-mahaguru"},
    {"title": "(Sulih Suara) Dari Istri Dari Istri Diam-Diam Jadi Pembalasan Maut", "slug": "dari-istri-diam-diam-jadi-pembalasan-maut"}, # Slug is dari-istri-diam-diam-jadi-pembalasan-maut
    {"title": "Lima tahun cinta dibalas pengkhianatan", "slug": "lima-tahun-cinta-dibalas-pengkhianatan"}
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

def download_r2_file(r2_key: str, dest_path: str, dry_run=False):
    """Download from R2 to local with progress report."""
    if dry_run:
        return True
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    head = r2.head_object(Bucket=BUCKET, Key=r2_key)
    total_size = head.get('ContentLength', 0)
    size_mb = total_size / (1024 * 1024)
    fname = os.path.basename(dest_path)
    
    # Check if already fully downloaded
    if os.path.exists(dest_path) and os.path.getsize(dest_path) == total_size:
        print(f"    [SKIP DL] {fname} (already downloaded)")
        return True
        
    print(f"    [DL] {fname} ({size_mb:.2f} MB)... ", end='', flush=True)
    try:
        r2.download_file(Bucket=BUCKET, Key=r2_key, Filename=dest_path)
        print("OK")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
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

def get_video_duration(video_path, dry_run=False):
    if dry_run:
        return 60.0  # Dummy 1 minute for dry-runs
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_path}"'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return float(res.stdout.strip())
    except Exception as e:
        print(f"Error getting duration for {video_path}: {e}")
    return 0.0

def get_video_height(video_path, dry_run=False):
    if dry_run:
        return 1280  # Default 720p portrait height
    cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "{video_path}"'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return int(res.stdout.strip())
    except Exception as e:
        print(f"Error getting height for {video_path}: {e}")
    return 1280

def get_video_width(video_path, dry_run=False):
    if dry_run:
        return 720
    cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=width -of default=noprint_wrappers=1:nokey=1 "{video_path}"'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return int(res.stdout.strip())
    except Exception as e:
        print(f"Error getting width for {video_path}: {e}")
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

def build_temp_ass(dest_folder: str, ep_vtt_files: dict, ep_video_files: dict, start: int, end: int, width: int, height: int, font_size=40, dry_run=False):
    """Build a combined shifted ASS file for the episode chunk. Returns (ass_filename, has_subtitles)."""
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
        
        # 1. Process VTT if exists
        if vtt_file:
            vtt_path = os.path.join(dest_folder, vtt_file)
            if dry_run or os.path.exists(vtt_path):
                has_subtitles = True
                if not dry_run:
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
        
        # 2. Add video duration to running offset
        if video_file:
            video_path = os.path.join(dest_folder, video_file)
            duration = get_video_duration(video_path, dry_run)
            running_offset += duration

    if has_subtitles and not dry_run:
        with open(temp_ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_header)
            f.write("\n".join(dialogues) + "\n")
        return temp_ass_filename, True
    elif has_subtitles and dry_run:
        return temp_ass_filename, True
    
    return None, False

def merge_episodes_hardsub(dest_folder: str, ep_files: dict, ep_vtt_files: dict, start: int, end: int, dry_run=False):
    """Concat video files, burn subtitles (MarginV=h/4, FontSize=40), speed up 1.05x."""
    output_filename = f"eps_{start}-{end}.mp4"
    output_path = os.path.join(dest_folder, output_filename)
    
    if not dry_run and os.path.exists(output_path):
        print(f"    [SKIP MERGE] {output_filename} already exists")
        return True

    # 1. Build the list of files to concat
    concat_list = []
    first_video_path = None
    for ep in range(start, end + 1):
        if ep in ep_files:
            concat_list.append(f"file '{ep_files[ep]}'")
            if not first_video_path:
                first_video_path = os.path.join(dest_folder, ep_files[ep])
        else:
            print(f"    [WARN] Episode {ep} missing for merge {start}-{end}")
            return False

    if not concat_list:
        return False

    list_path = os.path.join(dest_folder, "list.txt")
    if not dry_run:
        with open(list_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(concat_list) + "\n")

    # Get resolution properties
    height = get_video_height(first_video_path, dry_run)
    width = get_video_width(first_video_path, dry_run)

    # 2. Create the temporary shifted ASS subtitle file
    temp_ass, has_subs = build_temp_ass(dest_folder, ep_vtt_files, ep_files, start, end, width, height, font_size=40, dry_run=dry_run)
    
    # We speed up video by 1.05x: setpts = 1/1.05 = 0.95238
    # We speed up audio by 1.05x: atempo = 1.05
    if has_subs and temp_ass:
        # Note: ASS has absolute styles inside, so no force_style is needed
        cmd = f'ffmpeg -y -f concat -safe 0 -i list.txt -vf "subtitles={temp_ass},setpts=0.95238*PTS" -af "atempo=1.05" -c:v libx264 -crf 22 -preset veryfast -c:a aac -pix_fmt yuv420p "{output_filename}"'
        print(f"    [HARDSUB CONCAT + SPEEDUP] Concat eps {start}-{end} into {output_filename} (MarginV={height // 4}, FontSize=40, Speed=1.05)... ", end='', flush=True)
    else:
        cmd = f'ffmpeg -y -f concat -safe 0 -i list.txt -vf "setpts=0.95238*PTS" -af "atempo=1.05" -c:v libx264 -crf 22 -preset veryfast -c:a aac -pix_fmt yuv420p "{output_filename}"'
        print(f"    [CONCAT + SPEEDUP (NO SUBS)] Concat eps {start}-{end} into {output_filename} (Speed=1.05)... ", end='', flush=True)

    if dry_run:
        print("\n      [DRY RUN CMD]:", cmd)
        return True

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

    # Clean up temp list/ass files
    if os.path.exists(list_path):
        os.remove(list_path)
    if temp_ass and os.path.exists(os.path.join(dest_folder, temp_ass)):
        os.remove(os.path.join(dest_folder, temp_ass))
        
    return success

def main():
    parser = argparse.ArgumentParser(description="Download R2 dramas, Hardsub & Speedup 1.05x, Concat per 5 eps.")
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run to check file mappings and print commands')
    parser.add_argument('--limit-episodes', type=int, default=None, help='Limit number of episodes to download/process for testing')
    parser.add_argument('--drama-slug', type=str, default=None, help='Scrape/process only a specific drama slug')
    args = parser.parse_args()

    print("=" * 75)
    print("  DRAMA AUTOMATION: DOWNLOAD, HARDSUB (FONT 40, 1/4 HEIGHT), SPEED 1.05x, MERGE PER 5")
    print(f"  DRY RUN: {args.dry_run}")
    print("=" * 75)
    
    # Verify FFmpeg
    try:
        subprocess.run('ffmpeg -version', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[*] FFmpeg: AVAILABLE")
    except Exception:
        print("[ERROR] FFmpeg not found in system PATH. Merging will fail!")
        sys.exit(1)

    for drama in DRAMA_LIST:
        title = drama["title"]
        slug = drama["slug"]

        if args.drama_slug and slug != args.drama_slug:
            continue

        print(f"\n{'─'*75}")
        print(f"PROCESSING DRAMA: '{title}' ({slug})")

        prefix = f"dramas/{slug}/"
        files = list_r2_files(prefix)
        if not files:
            print(f"  [ERROR] No files found in R2 prefix: '{prefix}'")
            continue
            
        print(f"  R2 Prefix: '{prefix}'")
        print(f"  Total files in R2 prefix: {len(files)}")
        
        r2_keys_set = {f['Key'] for f in files}
        
        # Filter video files ending in .mp4
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
            print("  [ERROR] No episode files matching 'ep(\\d+)' found in prefix.")
            continue

        print(f"  Detected {len(ep_groups)} unique episodes.")
        
        # Create output local folder
        folder_name = safe_folder_name(title)
        dest_folder = os.path.join(DEST_ROOT, folder_name)
        os.makedirs(dest_folder, exist_ok=True)
        print(f"  Local Folder: {dest_folder}")

        downloaded_eps = {}
        downloaded_vtts = {}

        ep_keys = sorted(ep_groups.keys())
        if args.limit_episodes:
            ep_keys = ep_keys[:args.limit_episodes]

        # 1. Download best video and subtitle per episode
        for ep_num in ep_keys:
            candidates = ep_groups[ep_num]
            # Try to get _720p.mp4 if available, otherwise get largest size
            best_video = None
            for c in candidates:
                if '_720p' in c['Key']:
                    best_video = c
                    break
            if not best_video:
                best_video = max(candidates, key=lambda x: x.get('Size', 0))

            local_video_name = f"ep_{ep_num:03d}.mp4"
            local_video_path = os.path.join(dest_folder, local_video_name)

            ok_video = download_r2_file(best_video['Key'], local_video_path, args.dry_run)
            if ok_video:
                downloaded_eps[ep_num] = local_video_name

            # Look for matching subtitle epXXX_id.vtt
            vtt_key = best_video['Key'].replace('_720p.mp4', '_id.vtt').replace('_540p.mp4', '_id.vtt').replace('.mp4', '_id.vtt')
            if vtt_key not in r2_keys_set:
                vtt_key = prefix + f"ep{ep_num:03d}_id.vtt"
                if vtt_key not in r2_keys_set:
                    vtt_key = prefix + f"ep{ep_num:03d}.vtt"
                    if vtt_key not in r2_keys_set:
                        vtt_key = None

            if vtt_key and vtt_key in r2_keys_set:
                local_vtt_name = f"ep_{ep_num:03d}.vtt"
                local_vtt_path = os.path.join(dest_folder, local_vtt_name)
                ok_vtt = download_r2_file(vtt_key, local_vtt_path, args.dry_run)
                if ok_vtt:
                    downloaded_vtts[ep_num] = local_vtt_name

        # 2. Concat, Hardsub, Speedup, and Merge per 5
        print(f"  Hardsubbing and Merging episodes per 5 with speedup 1.05x...")
        all_ep_numbers = sorted(downloaded_eps.keys())
        if not all_ep_numbers:
            print("  [WARN] No episodes available for merge. Skipping.")
            continue

        max_ep = all_ep_numbers[-1]
        chunk_start = 1
        while chunk_start <= max_ep:
            chunk_end = min(chunk_start + 4, max_ep)
            chunk_eps = [ep for ep in range(chunk_start, chunk_end + 1) if ep in all_ep_numbers]
            if chunk_eps:
                merge_episodes_hardsub(dest_folder, downloaded_eps, downloaded_vtts, chunk_start, chunk_end, args.dry_run)
            chunk_start += 5

    print("\n" + "=" * 75)
    print("  PROCESS COMPLETED!")
    print(f"  Output folder: {DEST_ROOT}")
    print("=" * 75)

if __name__ == "__main__":
    main()
