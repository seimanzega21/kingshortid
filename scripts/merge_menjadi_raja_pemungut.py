#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge Drama: Menjadi Raja Pemungut (88 Episode)
Spesifikasi:
1. Scale : 105% (scale=756:1344, crop=720:1280)
2. Audio volume : +2.0 dB
3. Speed : 1.20x (video setpts=PTS/1.2, audio atempo=1.2)
4. Watermark : LayarDramaSeru (Arial Bold, clean, top-center safe zone)
5. Simpan di : D:\Video Drama\Facebook\Menjadi Raja Pemungut - Full Episode.mp4
"""

import sys
import time
import subprocess
from pathlib import Path

# Config
DRAMA_TITLE = "Menjadi Raja Pemungut"
EPISODES_DIR = Path(r"D:\Video Drama\Facebook\Menjadi Raja Pemungut")
OUTPUT_DIR  = Path(r"D:\Video Drama\Facebook")
TEMP_DIR    = Path(r"D:\temp_scraper\merge_menjadi_raja_pemungut")
TOTAL_EPS   = 88

OUTPUT_FILE = OUTPUT_DIR / f"{DRAMA_TITLE} - Full Episode.mp4"

def setup_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

def create_concat_list():
    concat_file = TEMP_DIR / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for i in range(1, TOTAL_EPS + 1):
            ep_path = (EPISODES_DIR / f"ep{i:03d}.mp4").resolve()
            if not ep_path.exists():
                raise FileNotFoundError(f"File episode tidak ditemukan: {ep_path}")
            clean_path = str(ep_path).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")
    print(f"[*] Concat list dibuat untuk {TOTAL_EPS} episode.")
    return concat_file

def merge_and_process():
    setup_dirs()
    concat_file = create_concat_list()

    print("\n[*] Memulai proses penggabungan & filter video...")
    print(f"    - Sumber: {EPISODES_DIR} ({TOTAL_EPS} episode lokal)")
    print(f"    - Scale: 105% (756x1344 -> crop 720x1280)")
    print(f"    - Speed: 1.20x")
    print(f"    - Audio: +2.0 dB")
    print(f"    - Watermark: 'LayarDramaSeru'")
    print(f"    - Output: {OUTPUT_FILE}")

    # Video Filter:
    # 1. setpts=PTS/1.2 (Speed 1.2x)
    # 2. scale=756:1344,crop=720:1280 (Scale 105% centered)
    # 3. drawtext (Watermark LayarDramaSeru)
    vf = (
        "setpts=PTS/1.2,"
        "scale=756:1344,crop=720:1280,"
        "drawtext=fontfile='C\\:/Windows/Fonts/arialbd.ttf':text='LayarDramaSeru':"
        "fontsize=26:fontcolor=white@0.85:shadowcolor=black@0.7:shadowx=2:shadowy=2:"
        "x=(w-text_w)/2:y=80"
    )

    # Audio Filter:
    # atempo=1.2 (Speed 1.2x), volume=2.0dB
    af = "atempo=1.2,volume=2.0dB"

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-vf", vf,
        "-af", af,
        "-c:v", "libx264",
        "-preset", "faster",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(OUTPUT_FILE)
    ]

    start_time = time.time()
    res = subprocess.run(cmd)
    elapsed = time.time() - start_time

    if res.returncode == 0 and OUTPUT_FILE.exists():
        size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
        print(f"\n[SUKSES] Video berhasil digabungkan!")
        print(f" Lokasi: {OUTPUT_FILE}")
        print(f" Ukuran: {size_mb:.2f} MB")
        print(f" Waktu Proses: {elapsed/60:.2f} menit")

        # Bersihkan temp concat file
        (TEMP_DIR / "concat_list.txt").unlink(missing_ok=True)
        return True
    else:
        print("\n[GAGAL] Terjadi kesalahan saat penggabungan video FFmpeg.")
        return False

if __name__ == "__main__":
    merge_and_process()
