#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Penggabung Drama: Harta Karun dari Sungai 1 (70 Episode) Menjadi 1 Video Utuh 1080p
Dengan Proteksi Anti-Hak Cipta (Anti-Content ID Facebook/YouTube/TikTok):
- Upscale 1080x1920 Full HD (Lanczos Interpolation)
- Micro Speed 1.03x + Audio Pitch Shift (+3%)
- Audio Equalizer (Vocal Boost 2.2kHz + Low/High Cut)
- Audio Stereo Phase Widening (Extrastereo)
- Visual Micro Adjustments (Contrast +2%, Saturation +3%)
- Faststart Metadata Injection (+faststart)
Output: D:\Video Drama\Facebook\Harta Karun dari Sungai 1\Full Movie\Harta Karun dari Sungai 1 - Full Movie (1080p).mp4
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import re
import time
import subprocess
from pathlib import Path

SOURCE_DIR = Path("D:/Video Drama/Facebook/Harta Karun dari Sungai 1")
OUTPUT_DIR = SOURCE_DIR / "Full Movie"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "Harta Karun dari Sungai 1 - Full Movie (1080p).mp4"
TEMP_DIR = Path("D:/temp_scraper")
TEMP_DIR.mkdir(parents=True, exist_ok=True)
CONCAT_FILE = TEMP_DIR / "harta_karun_concat.txt"

TOTAL_EPISODES = 70

def verify_episodes():
    print("=" * 65)
    print("MEMERIKSA FILE EPISODE SUMBER...")
    print("=" * 65)
    missing = []
    file_list = []
    for i in range(1, TOTAL_EPISODES + 1):
        ep_file = SOURCE_DIR / f"ep{i:03d}.mp4"
        if not ep_file.exists() or ep_file.stat().st_size < 100 * 1024:
            missing.append(i)
        else:
            file_list.append(ep_file)

    if missing:
        print(f"[ERROR] Ada {len(missing)} episode yang hilang: {missing}")
        return None

    print(f"-> Semua {len(file_list)} episode LENGKAP dan VALID!")
    return file_list

def create_concat_file(file_list):
    print("\n-> Membuat file concat demuxer...")
    with open(CONCAT_FILE, "w", encoding="utf-8") as f:
        for p in file_list:
            # Escape path for ffmpeg concat
            escaped = str(p).replace("\\", "/")
            f.write(f"file '{escaped}'\n")
    print(f"-> Concat list siap: {CONCAT_FILE}")

def run_merge():
    file_list = verify_episodes()
    if not file_list:
        sys.exit(1)

    create_concat_file(file_list)

    # Filter chains:
    # Video: Speed 1.03x (setpts=PTS/1.03), scale to 1080x1920 (lanczos), subtle contrast & saturation
    vf = (
        "setpts=PTS/1.03,"
        "scale=1080:1920:flags=lanczos,"
        "eq=contrast=1.02:brightness=0.01:saturation=1.03"
    )

    # Audio: Speed 1.03x & pitch +3% (asetrate=44100*1.03,aresample=44100),
    # Highpass 70Hz & Lowpass 15kHz, Vocal EQ boost 2.2kHz +2.5dB, Stereo widening
    af = (
        "asetrate=44100*1.03,aresample=44100,"
        "highpass=f=70,lowpass=f=15000,"
        "equalizer=f=2200:t=q:w=1.2:g=2.5,"
        "extrastereo=m=1.2"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(CONCAT_FILE),
        "-vf", vf,
        "-af", af,
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "veryfast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(OUTPUT_FILE)
    ]

    print("\n" + "=" * 65)
    print("MEMULAI PENGGABUNGAN & RENDER 1080p FULL MOVIE")
    print(f"Target File: {OUTPUT_FILE}")
    print("Ketentuan:")
    print("  - Resolusi: 1080 x 1920 (1080p Full HD Vertical)")
    print("  - Anti-Copyright Audio: Speed 1.03x + Pitch +3% + Vocal EQ + Extrastereo")
    print("  - Anti-Copyright Visual: Lanczos 1080p + Subtle Contrast & Saturation")
    print("=" * 65)

    start_time = time.time()
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, encoding="utf-8", errors="replace")

    # Total expected duration at 1.03x is ~8004 seconds
    expected_duration = 8004.0
    last_print = 0

    time_regex = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")
    speed_regex = re.compile(r"speed=\s*([\d\.]+)x")

    for line in process.stderr:
        t_match = time_regex.search(line)
        if t_match:
            hours, mins, secs = int(t_match.group(1)), int(t_match.group(2)), int(t_match.group(3))
            current_sec = hours * 3600 + mins * 60 + secs
            pct = min(99.9, (current_sec / expected_duration) * 100)

            s_match = speed_regex.search(line)
            speed_str = s_match.group(1) + "x" if s_match else "N/A"

            now = time.time()
            if now - last_print >= 5:
                elapsed = now - start_time
                print(f"  [RENDER] Progress: {pct:5.1f}% | Waktu Film: {hours:02d}:{mins:02d}:{secs:02d} | Kecepatan: {speed_str} | Berjalan: {elapsed/60:.1f} m", flush=True)
                last_print = now

    process.wait()

    if process.returncode == 0 and OUTPUT_FILE.exists() and OUTPUT_FILE.stat().st_size > 100 * 1024 * 1024:
        total_time = time.time() - start_time
        size_gb = OUTPUT_FILE.stat().st_size / (1024 ** 3)
        print("\n" + "=" * 65)
        print("PENGGABUNGAN SUKSES 100%!")
        print(f"Lokasi File: {OUTPUT_FILE}")
        print(f"Ukuran File: {size_gb:.2f} GB")
        print(f"Waktu Render: {total_time/60:.2f} menit")
        print("=" * 65)
        CONCAT_FILE.unlink(missing_ok=True)
    else:
        print("\n[ERROR] Proses penggabungan gagal atau terhenti!")
        sys.exit(1)

if __name__ == "__main__":
    run_merge()
