#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge Drama: Kontrak Monster Laut di Desa Nelayan
Spesifikasi Sesuai Permintaan:
1. Scale: 105% (756x1344 cropped centered to 720x1280)
2. Audio volume: +2.0 dB
3. Speed: 1.20x (video setpts=PTS/1.2, audio atempo=1.2)
4. Watermark: 'LayarDramaSeru' (Arial Bold, clean, top-center safe zone)
5. Simpan di: D:\Video Drama\Facebook\
"""

import os
import sys
import time
import requests
import subprocess
import concurrent.futures
from pathlib import Path

# Config
DRAMA_TITLE = "Kontrak Monster Laut di Desa Nelayan"
OUTPUT_DIR  = Path(r"D:\Video Drama\Facebook")
TEMP_DIR    = Path(r"D:\temp_scraper\merge_kontrak_monster_laut")
R2_BASE_URL = "https://stream.shortlovers.id/dramas/netshort/kontrak-monster-laut-di-desa-nelayan"
TOTAL_EPS   = 68

OUTPUT_FILE = OUTPUT_DIR / f"{DRAMA_TITLE} - Full Episode.mp4"

def setup_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

def download_episode(ep_num):
    ep_name = f"ep{ep_num:03d}.mp4"
    local_path = TEMP_DIR / ep_name

    # If already downloaded and complete
    if local_path.exists() and local_path.stat().st_size > 1000000:
        return ep_num, True

    url = f"{R2_BASE_URL}/{ep_name}"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=30)
            if r.ok and len(r.content) > 500000:
                local_path.write_bytes(r.content)
                return ep_num, True
        except Exception:
            time.sleep(2)

    return ep_num, False

def download_all_episodes():
    print(f"[*] Mendownload {TOTAL_EPS} episode ke temporary folder...")
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(download_episode, i): i for i in range(1, TOTAL_EPS + 1)}
        for future in concurrent.futures.as_completed(futures):
            ep_num, ok = future.result()
            if ok:
                success_count += 1
                if success_count % 10 == 0 or success_count == TOTAL_EPS:
                    print(f"    Progress download: {success_count}/{TOTAL_EPS} episode siap...")
            else:
                print(f"[!] Gagal download ep{ep_num:03d}")

    if success_count != TOTAL_EPS:
        raise RuntimeError(f"Download tidak lengkap: hanya {success_count}/{TOTAL_EPS} episode berhasil.")
    print("[*] Seluruh episode berhasil diunduh!")

def create_concat_list():
    concat_file = TEMP_DIR / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for i in range(1, TOTAL_EPS + 1):
            ep_path = (TEMP_DIR / f"ep{i:03d}.mp4").resolve()
            # Format path for FFmpeg concat
            clean_path = str(ep_path).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")
    return concat_file

def merge_and_process():
    setup_dirs()
    download_all_episodes()
    concat_file = create_concat_list()

    print("\n[*] Memulai proses penggabungan & filter video...")
    print(f"    - Scale: 105% (756x1344 -> crop 720x1280)")
    print(f"    - Speed: 1.20x")
    print(f"    - Audio: +2.0 dB")
    print(f"    - Watermark: 'LayarDramaSeru'")
    print(f"    - Output: {OUTPUT_FILE}")

    # Filter Chain:
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

        # Bersihkan file temporary raw
        print("[*] Membersihkan file temporary...")
        try:
            for item in TEMP_DIR.glob("*.mp4"):
                item.unlink()
            (TEMP_DIR / "concat_list.txt").unlink(missing_ok=True)
            print("[*] File temporary dibersihkan.")
        except Exception as e:
            print(f"[!] Warning saat cleanup temp: {e}")

        return True
    else:
        print("\n[GAGAL] Terjadi kesalahan saat penggabungan video FFmpeg.")
        return False

if __name__ == "__main__":
    merge_and_process()
