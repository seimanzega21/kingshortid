#!/usr/bin/env python3
"""
Watermark + Merge Drama Episodes for Facebook Posting
======================================================
Strategy: Medium + Advanced Watermark Combo
  1. Logo KingShort semi-transparan di kiri atas
  2. Teks diagonal berulang "KingShort" di seluruh layar (opacity 12%)
  3. CTA scrolling text di bawah: "Tonton selengkapnya di KingShort"

Process:
  1. Add watermarks to each episode
  2. Merge every 3 episodes into one video
  3. Output to specified folder

Usage: python watermark_merge_drama.py
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
OUTPUT_DIR = r"D:\kingshortid\Download Drama\Salah Sangka Berujung Jadi Ayah\Facebook Ready"
TEMP_DIR   = r"D:\kingshortid\Download Drama\Salah Sangka Berujung Jadi Ayah\temp_processing"
LOGO_PATH  = r"D:\kingshortid\mobile\assets\icon-kshort.png"

EPISODES_PER_BATCH = 3
DRAMA_TITLE = "Salah Sangka Berujung Jadi Ayah"

# Watermark settings
LOGO_SIZE = 80
LOGO_OPACITY = 0.7
LOGO_MARGIN = 15
DIAGONAL_OPACITY = 0.12
CTA_TEXT = "Tonton selengkapnya di KingShort"
CTA_FONTSIZE = 22
# ============================================================


def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)


def get_episodes():
    pattern = os.path.join(SOURCE_DIR, "*.mp4")
    files = sorted(glob.glob(pattern))
    files = [f for f in files if os.path.dirname(f) == SOURCE_DIR
             and "test_watermark" not in os.path.basename(f)]
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


def build_watermark_filter(width, height, ep_num):
    """Build FFmpeg filter string for triple watermark."""
    parts = []

    # Layer 1: Logo overlay
    parts.append(
        f"[1:v]scale={LOGO_SIZE}:-1,format=rgba,"
        f"colorchannelmixer=aa={LOGO_OPACITY}[logo];"
        f"[0:v][logo]overlay={LOGO_MARGIN}:{LOGO_MARGIN}[base]"
    )

    # Layer 2: Diagonal text grid
    # Place text at staggered positions across the frame
    diagonal_items = []
    rows = max(4, height // 180)
    cols = max(3, width // 220)

    for r in range(rows):
        for c in range(cols):
            x = c * 220 - 30 + (r % 2) * 110
            y = r * 180 + 50
            if 0 <= x < width + 100 and 0 <= y < height + 50:
                diagonal_items.append(
                    f"drawtext=text='KingShort':"
                    f"fontsize=28:fontcolor=white@{DIAGONAL_OPACITY}:"
                    f"x={x}:y={y}"
                )

    # Layer 3: Scrolling CTA at bottom
    cta = (
        f"drawtext=text='{CTA_TEXT}  |  Download KingShort di Play Store  |  {CTA_TEXT}':"
        f"fontsize={CTA_FONTSIZE}:fontcolor=gold@0.85:"
        f"borderw=1:bordercolor=black@0.5:"
        f"y=h-{CTA_FONTSIZE + 12}:"
        f"x='w-mod(t*120\\,w+tw)'"
    )

    # Layer 4: Episode number label
    ep_label = (
        f"drawtext=text='Ep {ep_num}':"
        f"fontsize=18:fontcolor=white@0.6:"
        f"x=w-tw-15:y=15"
    )

    # Combine all drawtext filters on [base]
    all_drawtext = ",".join(diagonal_items + [cta, ep_label])
    parts.append(f"[base]{all_drawtext}[outv]")

    return ";".join(parts)


def watermark_episode(input_path, output_path, ep_num):
    """Apply triple watermark to a single episode."""
    width, height = get_video_info(input_path)
    filter_complex = build_watermark_filter(width, height, ep_num)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-i", LOGO_PATH,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?",
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
        if result.returncode != 0:
            # Try simplified version if complex filter fails
            return watermark_simple(input_path, output_path, ep_num)
        return True
    except subprocess.TimeoutExpired:
        print(f"    [!] Timeout ep {ep_num}")
        return False
    except Exception as e:
        print(f"    [!] Error: {e}")
        return False


def watermark_simple(input_path, output_path, ep_num):
    """Simplified watermark as fallback."""
    filter_complex = (
        f"[1:v]scale={LOGO_SIZE}:-1,format=rgba,"
        f"colorchannelmixer=aa={LOGO_OPACITY}[logo];"
        f"[0:v][logo]overlay={LOGO_MARGIN}:{LOGO_MARGIN},"
        f"drawtext=text='KingShort':fontsize=28:fontcolor=white@{DIAGONAL_OPACITY}:x=200:y=300,"
        f"drawtext=text='KingShort':fontsize=28:fontcolor=white@{DIAGONAL_OPACITY}:x=50:y=600,"
        f"drawtext=text='KingShort':fontsize=28:fontcolor=white@{DIAGONAL_OPACITY}:x=350:y=900,"
        f"drawtext=text='KingShort':fontsize=28:fontcolor=white@{DIAGONAL_OPACITY}:x=100:y=150,"
        f"drawtext=text='KingShort':fontsize=28:fontcolor=white@{DIAGONAL_OPACITY}:x=400:y=500,"
        f"drawtext=text='KingShort':fontsize=28:fontcolor=white@{DIAGONAL_OPACITY}:x=250:y=750,"
        f"drawtext=text='{CTA_TEXT}':fontsize={CTA_FONTSIZE}:fontcolor=gold@0.85:"
        f"borderw=1:bordercolor=black@0.5:y=h-34:x='w-mod(t*120\\,w+tw)',"
        f"drawtext=text='Ep {ep_num}':fontsize=18:fontcolor=white@0.6:x=w-tw-15:y=15"
        f"[outv]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-i", LOGO_PATH,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?",
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
    except Exception:
        return False


def merge_episodes(episode_paths, output_path, batch_label):
    """Merge watermarked episodes into one video."""
    list_file = os.path.join(TEMP_DIR, f"concat_{batch_label}.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for ep_path in episode_paths:
            safe_path = ep_path.replace("\\", "/")
            f.write(f"file '{safe_path}'\n")

    # Try stream copy first (fastest)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        "-movflags", "+faststart",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return True

        # Fallback: re-encode merge
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
    print(f"  KINGSHORT WATERMARK + MERGE TOOL")
    print(f"  Drama: {DRAMA_TITLE}")
    print(f"  Strategy: Medium + Advanced (Logo + Diagonal + CTA)")
    print("=" * 65)

    ensure_dirs()

    if not os.path.exists(LOGO_PATH):
        print(f"[ERROR] Logo not found: {LOGO_PATH}")
        sys.exit(1)

    episodes = get_episodes()
    total_eps = len(episodes)
    total_batches = math.ceil(total_eps / EPISODES_PER_BATCH)

    print(f"\n[i] Found {total_eps} episodes")
    print(f"[i] Output: {OUTPUT_DIR}")
    print(f"[i] Batch size: {EPISODES_PER_BATCH} episodes")
    print(f"[i] Total merged files: {total_batches}")

    if total_eps == 0:
        print("[!] No episodes found!")
        sys.exit(1)

    # ======================================
    # PHASE 1: Watermark
    # ======================================
    print(f"\n{'='*65}")
    print(f"  PHASE 1: Watermark ({total_eps} episodes)")
    print(f"{'='*65}")

    watermarked = []
    t0 = time.time()

    for i, ep_path in enumerate(episodes):
        ep_num = i + 1
        fname = os.path.basename(ep_path)
        wm_out = os.path.join(TEMP_DIR, f"wm_ep{ep_num:03d}.mp4")

        if os.path.exists(wm_out) and os.path.getsize(wm_out) > 100_000:
            print(f"  [{ep_num:3d}/{total_eps}] SKIP (exists) {fname}")
            watermarked.append(wm_out)
            continue

        elapsed = time.time() - t0
        eta = ""
        if i > 0:
            eta = f" | ETA: {(elapsed / i * (total_eps - i)) / 60:.0f}min"

        print(f"  [{ep_num:3d}/{total_eps}] {fname} ({format_size(os.path.getsize(ep_path))}){eta}", end="", flush=True)

        ok = watermark_episode(ep_path, wm_out, ep_num)

        if ok and os.path.exists(wm_out) and os.path.getsize(wm_out) > 10_000:
            watermarked.append(wm_out)
            print(f" -> OK ({format_size(os.path.getsize(wm_out))})")
        else:
            watermarked.append(ep_path)  # fallback
            print(f" -> FAIL (using original)")

    t1 = time.time()
    print(f"\n  Phase 1 done: {(t1-t0)/60:.1f} min")

    # ======================================
    # PHASE 2: Merge every 3
    # ======================================
    print(f"\n{'='*65}")
    print(f"  PHASE 2: Merge (every {EPISODES_PER_BATCH})")
    print(f"{'='*65}")

    merged_ok = 0
    for b in range(total_batches):
        s = b * EPISODES_PER_BATCH
        e = min(s + EPISODES_PER_BATCH, total_eps)
        batch_files = watermarked[s:e]
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

    total_time = time.time() - t0

    # ======================================
    # SUMMARY
    # ======================================
    print(f"\n{'='*65}")
    print(f"  ✅ SELESAI!")
    print(f"{'='*65}")
    print(f"  Watermarked : {len(watermarked)}/{total_eps}")
    print(f"  Merged      : {merged_ok}/{total_batches}")
    print(f"  Output      : {OUTPUT_DIR}")
    print(f"  Total time  : {total_time/60:.1f} min")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
