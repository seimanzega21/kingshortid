#!/usr/bin/env python3
"""
TikTok Anti-Detection & Merge Tool (Video Cloaking)
===================================================
Strategy: Algorithms Bypass
  - 2% Crop + Scale (Changes entire frame pixel layout)
  - 1.05x Speedup (Changes video/audio duration footprint)
  - Color Shift (Brightness +2%, Saturation +5%, Contrast +2%)
  - Clean Metadata Stripping
  - Floating/Moving subtle watermark (Avoids static logo detection)

Usage: python tiktok_bypass.py
"""

import os
import sys
import glob
import subprocess
import time
import math
import json

# ============================================================
# CONFIGURATION
# ============================================================
SOURCE_DIR = r"D:\kingshortid\Download Drama\Salah Sangka Berujung Jadi Ayah"
OUTPUT_DIR = r"D:\kingshortid\Download Drama\Salah Sangka Berujung Jadi Ayah\TikTok Ready"
TEMP_DIR   = r"D:\kingshortid\Download Drama\Salah Sangka Berujung Jadi Ayah\temp_tiktok"

EPISODES_PER_BATCH = 3
DRAMA_TITLE = "Salah Sangka Berujung Jadi Ayah"
# ============================================================

def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

def get_episodes():
    pattern = os.path.join(SOURCE_DIR, "*.mp4")
    files = sorted(glob.glob(pattern))
    # Ambil file asli yang ada di folder parent, bukan yang sudah diproses
    files = [f for f in files if os.path.dirname(f) == SOURCE_DIR]
    return files

def get_video_info(filepath):
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", filepath
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                return int(stream["width"]), int(stream["height"])
    except Exception:
        pass
    return 720, 1280

def build_bypass_filter(width, height):
    """
    Build complex FFmpeg filter.
    - crop=iw*0.98:ih*0.98 : Potong pinggir 2%
    - scale=720:1280       : Kembalikan ke rasio 9:16 portrait
    - eq=...               : Manipulasi warna halus
    - setpts=0.95*PTS      : Percepat video 5% (1 / 1.05 = ~0.952)
    - drawtext=...         : Teks bergerak melayang dengan pola sine/cosine
                             sehingga tidak pernah diam di satu titik (Anti-Bot)
    """
    
    # Text bergerak melingkar/membentuk pola unik tak beraturan
    floating_watermark = (
        f"drawtext=text='KingShort':"
        f"fontsize=36:fontcolor=white@0.15:"
        f"x='(w-tw)/2 + ((w-tw)/3)*sin(t/3)':"
        f"y='(h-th)/2 + ((h-th)/3)*cos(t/4)'"
    )
    
    v_filter = (
        f"[0:v]crop=iw*0.98:ih*0.98,"
        f"scale={width}:{height},"
        f"eq=brightness=0.02:contrast=1.02:saturation=1.05,"
        f"setpts=0.95238*PTS,"
        f"{floating_watermark}[v_out]"
    )
    
    # Percepat audio 5% tanpa merusak nada (pitch correction on by default in atempo)
    a_filter = "[0:a]atempo=1.05[a_out]"
    
    return v_filter + ";" + a_filter

def bypass_episode(input_path, output_path, ep_num):
    """Apply bypassing attributes to a single episode."""
    width, height = get_video_info(input_path)
    
    # Normalisasi dimensi agar genap (wajib untuk beberapa codec)
    width = width if width % 2 == 0 else width - 1
    height = height if height % 2 == 0 else height - 1
    
    filter_complex = build_bypass_filter(width, height)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[v_out]",
        "-map", "[a_out]",
        "-map_metadata", "-1",        # HAPUS SEMUA METADATA ASLI
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"    [!] Timeout ep {ep_num}")
        return False
    except Exception as e:
        print(f"    [!] Error: {e}")
        return False


def merge_episodes(episode_paths, output_path, batch_label):
    """Gabungkan episode yang sudah diproses."""
    list_file = os.path.join(TEMP_DIR, f"concat_{batch_label}.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for ep_path in episode_paths:
            safe_path = ep_path.replace("\\", "/")
            f.write(f"file '{safe_path}'\n")

    # Stream copy
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-map_metadata", "-1", # Pastikan hasil gabungan juga bersih
        "-c", "copy",
        "-movflags", "+faststart",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return True
            
        print(f"    [~] Re-encoding merge for {batch_label}...")
        cmd_re = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_file,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]
        result = subprocess.run(cmd_re, capture_output=True, text=True, timeout=900)
        return result.returncode == 0
    except Exception as e:
        print(f"    [!] Merge error: {e}")
        return False

def format_size(size_bytes):
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"

def main():
    print("=" * 65)
    print(f"  TIKTOK BYPASS & MERGE TOOL")
    print(f"  Drama: {DRAMA_TITLE}")
    print(f"  Features: Speed 1.05x | Crop 2% | Color Shift | Clean Meta | Floating Text")
    print("=" * 65)

    ensure_dirs()
    
    episodes = get_episodes()
    total_eps = len(episodes)
    total_batches = math.ceil(total_eps / EPISODES_PER_BATCH)

    print(f"\n[i] Found {total_eps} original episodes")
    print(f"[i] Output: {OUTPUT_DIR}")

    if total_eps == 0:
        print("[!] No episodes found!")
        sys.exit(1)

    # PHASE 1: Bypass Processing
    print(f"\n{'='*65}")
    print(f"  PHASE 1: Anti-Detection Filter & Render ({total_eps} episodes)")
    print(f"{'='*65}")

    processed_files = []
    t0 = time.time()

    for i, ep_path in enumerate(episodes):
        ep_num = i + 1
        fname = os.path.basename(ep_path)
        tmp_out = os.path.join(TEMP_DIR, f"tt_ep{ep_num:03d}.mp4")

        if os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 100_000:
            print(f"  [{ep_num:3d}/{total_eps}] SKIP (exists) {fname}")
            processed_files.append(tmp_out)
            continue

        elapsed = time.time() - t0
        eta = f" | ETA: {(elapsed / i * (total_eps - i)) / 60:.0f}min" if i > 0 else ""
        print(f"  [{ep_num:3d}/{total_eps}] Rendering Cloaked {fname} {eta}", end="", flush=True)

        ok = bypass_episode(ep_path, tmp_out, ep_num)

        if ok and os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 10_000:
            processed_files.append(tmp_out)
            print(f" -> OK ({format_size(os.path.getsize(tmp_out))})")
        else:
            print(f" -> FAIL")

    print(f"\n  Phase 1 done: {(time.time()-t0)/60:.1f} min")

    # PHASE 2: Merge Every 3
    print(f"\n{'='*65}")
    print(f"  PHASE 2: Merge (every {EPISODES_PER_BATCH})")
    print(f"{'='*65}")

    merged_ok = 0
    for b in range(total_batches):
        s = b * EPISODES_PER_BATCH
        e = min(s + EPISODES_PER_BATCH, total_eps)
        batch_files = processed_files[s:e]
        
        # Hanya gabungkan jika batch masih ada filenya
        if not batch_files: continue
            
        ep_range = f"Ep{s+1:03d}-{e:03d}"
        label = f"Part{b+1:02d}_{ep_range}"
        out_name = f"{DRAMA_TITLE} - {label}.mp4"
        out_path = os.path.join(OUTPUT_DIR, out_name)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 100_000:
            print(f"  [{b+1:2d}/{total_batches}] SKIP (exists) {out_name}")
            merged_ok += 1
            continue

        print(f"  [{b+1:2d}/{total_batches}] {out_name}", end="", flush=True)
        ok = merge_episodes(batch_files, out_path, label)
        if ok and os.path.exists(out_path):
            merged_ok += 1
            print(f" -> OK ({format_size(os.path.getsize(out_path))})")
        else:
            print(f" -> FAIL")

    print(f"\n{'='*65}")
    print(f"  ✅ SELESAI!")
    print(f"  Output folder: {OUTPUT_DIR}")
    print(f"{'='*65}")

if __name__ == "__main__":
    main()
