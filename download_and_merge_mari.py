# -*- coding: utf-8 -*-
"""
Download & Merge script for "Mari Berkultivasi Sekeluarga"
Downloads 720p episodes from R2 -> D:/Video Drama/Facebook/raw_episodes/
Merges them in groups of 3 using FFmpeg concat demuxer -> D:/Video Drama/Facebook/
"""
import os
import sys
import boto3
import subprocess
import time
from botocore.config import Config

sys.stdout.reconfigure(encoding='utf-8')

# ─── CONFIG ─────────────────────────────────────────────────────────────────
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
BOOK_SLUG   = 'mari-berkultivasi-sekeluarga'

# Local target folders
DEST_ROOT  = 'D:/Video Drama/Facebook'
RAW_DIR    = os.path.join(DEST_ROOT, 'raw_episodes')

os.makedirs(DEST_ROOT, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)

# ─── R2 CLIENT ──────────────────────────────────────────────────────────────
r2 = boto3.client(
    's3', endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'), region_name='auto'
)

def download_episode(ep_no):
    key = f"dramas/{BOOK_SLUG}/ep{ep_no:03d}_720p.mp4"
    dest_path = os.path.join(RAW_DIR, f"ep{ep_no:03d}_720p.mp4")
    
    # Check if already exists and size matches
    try:
        head = r2.head_object(Bucket=R2_BUCKET, Key=key)
        r2_size = head.get('ContentLength', 0)
        
        if os.path.exists(dest_path):
            local_size = os.path.getsize(dest_path)
            if local_size == r2_size:
                print(f"   ✓ Episode {ep_no:02d} already downloaded.")
                return dest_path
                
        print(f"   ⬆ Downloading Episode {ep_no:02d} ({r2_size/(1024*1024):.1f} MB)...", end='', flush=True)
        r2.download_file(Bucket=R2_BUCKET, Key=key, Filename=dest_path)
        print(" Done.")
        return dest_path
    except Exception as e:
        print(f"\n   ✗ Error downloading Episode {ep_no:02d}: {e}")
        return None

def merge_episodes(episodes_chunk, group_idx):
    """Merge a chunk of 3 episodes using FFmpeg concat demuxer"""
    start_ep = episodes_chunk[0]
    end_ep = episodes_chunk[-1]
    
    out_filename = f"Mari Berkultivasi Sekeluarga - Episode {start_ep:02d}-{end_ep:02d}.mp4"
    out_path = os.path.join(DEST_ROOT, out_filename)
    
    print(f"\n🎬 Merging Episodes {start_ep:02d}-{end_ep:02d} -> {out_filename}")
    
    # Create FFmpeg list file
    list_file_path = os.path.join(DEST_ROOT, f"temp_list_g{group_idx}.txt")
    with open(list_file_path, 'w', encoding='utf-8') as f:
        for ep in episodes_chunk:
            ep_file = os.path.join(RAW_DIR, f"ep{ep:03d}_720p.mp4")
            # FFmpeg concat requires forward slashes or escaped backslashes
            normalized_path = ep_file.replace('\\', '/')
            f.write(f"file '{normalized_path}'\n")
            
    # Run FFmpeg concat
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', list_file_path,
        '-c', 'copy',
        '-movflags', '+faststart',
        '-loglevel', 'warning',
        out_path
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
    
    # Clean up list file
    if os.path.exists(list_file_path):
        os.remove(list_file_path)
        
    if res.returncode == 0:
        size_mb = os.path.getsize(out_path) / (1024*1024)
        print(f"   ✓ Merged successfully! Size: {size_mb:.1f} MB")
        return out_path
    else:
        print(f"   ✗ Merge failed: {res.stderr}")
        return None

def main():
    print("=" * 60)
    print("DOWNLOAD AND LOSSLESS MERGE PIPELINE")
    print(f"Drama: {BOOK_SLUG} (720p)")
    print(f"Target Directory: {DEST_ROOT}")
    print("=" * 60)
    
    total_episodes = 60
    
    # 1. Download all 60 episodes
    print("\n[PHASE 1] Downloading 60 episodes from R2...")
    downloaded_paths = {}
    for ep in range(1, total_episodes + 1):
        path = download_episode(ep)
        if path:
            downloaded_paths[ep] = path
            
    if len(downloaded_paths) < total_episodes:
        print(f"\n⚠ Warning: Only downloaded {len(downloaded_paths)}/{total_episodes} episodes.")
        
    # 2. Group into chunks of 3 and merge
    print("\n[PHASE 2] Merging episodes in groups of 3...")
    success_count = 0
    
    # Group episodes: 1-3, 4-6, etc.
    groups = []
    current_group = []
    for ep in range(1, total_episodes + 1):
        if ep in downloaded_paths:
            current_group.append(ep)
        if len(current_group) == 3 or (ep == total_episodes and current_group):
            groups.append(current_group)
            current_group = []
            
    for idx, group in enumerate(groups, 1):
        if len(group) == 3:
            merged = merge_episodes(group, idx)
            if merged:
                success_count += 1
        else:
            print(f"\n⚠ Skipping group {group} as it does not have exactly 3 episodes.")
            
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED!")
    print(f"  Raw Episodes Directory: {RAW_DIR}")
    print(f"  Merged Videos Directory: {DEST_ROOT}")
    print(f"  Successfully Merged: {success_count}/{len(groups)} groups")
    print("=" * 60)

if __name__ == "__main__":
    main()
