import os
import sys
import glob
import subprocess
import time
import math

# Konfigurasi Folder
SOURCE_DIR = r"D:\kingshortid\scripts\melolo-scraper\downloads\sesepuh-tertua-yang-masih-muda"
OUTPUT_DIR = os.path.join(SOURCE_DIR, "Facebook_TikTok_Ready")
TEMP_DIR = os.path.join(SOURCE_DIR, "temp_processing")
DRAMA_TITLE = "Sesepuh Tertua Yang Masih Muda"

EPISODES_PER_BATCH = 2

def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

def get_episodes():
    pattern = os.path.join(SOURCE_DIR, "*.mp4")
    files = sorted(glob.glob(pattern))
    return [f for f in files if os.path.dirname(f) == SOURCE_DIR]

def create_title_intro(text, output_path):
    """Membuat video cover 1.5 detik dengan tulisan hitam putih 'Eps X-Y'."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=black:s=720x1280:d=1.5",
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",  # Blank audio agar pas di-concat cocok
        "-vf", f"drawtext=text='{text}':fontcolor=white:fontsize=100:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-t", "1.5",
        "-pix_fmt", "yuv420p",
        "-video_track_timescale", "15360", # Agar kompatibel
        output_path
    ]
    subprocess.run(cmd, capture_output=True)
    return os.path.exists(output_path)

def process_and_merge(batch_files, batch_label, output_path):
    """
    1. Membuat intro video Eps X-Y
    2. Membuat list file untuk digabung (Intro + Ep1 + Ep2)
    3. Menggabungkan sekaligus mengaplikasikan filter bebas hak cipta (speedup 5%, crop pinggir)
    """
    print(f"  Memproses {batch_label} ...")
    intro_path = os.path.join(TEMP_DIR, f"intro_{batch_label}.mp4")
    
    if not create_title_intro(batch_label, intro_path):
        print(f"    [!] Gagal membuat intro untuk {batch_label}")
        return False
        
    list_file = os.path.join(TEMP_DIR, f"concat_{batch_label}.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        f.write(f"file '{intro_path.replace(chr(92), '/')}'\n")
        for ep_path in batch_files:
            f.write(f"file '{ep_path.replace(chr(92), '/')}'\n")
            
    # Filter Anti-Deteksi Hak Cipta (TikTok & Facebook Bypass)
    # - Mempercepat video 5% (atempo=1.05 & setpts=0.95*PTS)
    # - Memotong pinggiran video 2% (crop) dan meningkatkan contrast 2%
    # - Strip Metadata
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-filter_complex", "[0:v]crop=iw*0.98:ih*0.98,scale=720:1280,eq=brightness=0.01:contrast=1.02:saturation=1.05,setpts=0.95238*PTS[v];[0:a]atempo=1.05[a]",
        "-map", "[v]",
        "-map", "[a]",
        "-map_metadata", "-1",
        "-c:v", "libx264", "-preset", "fast", "-crf", "26",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return result.returncode == 0
    except Exception as e:
        print(f"    [!] Error merge: {e}")
        return False

def extract_ep_num(filename):
    """Mengekstrak angka episode dari nama file, contoh: ep_002.mp4 => 2"""
    num_str = ''.join(filter(str.isdigit, os.path.basename(filename)))
    return int(num_str) if num_str else 0

def main():
    ensure_dirs()
    episodes = get_episodes()
    if not episodes:
        print("[!] Tidak ada video MP4 yang ditemukan di folder sumber.")
        return
        
    # Sort files berdasarkan nomer episode
    episodes.sort(key=extract_ep_num)
    
    total_eps = len(episodes)
    print(f"Ditemukan {total_eps} episode. Memulai proses penggabungan per {EPISODES_PER_BATCH} episode...")
    
    for i in range(0, total_eps, EPISODES_PER_BATCH):
        batch = episodes[i:i+EPISODES_PER_BATCH]
        if not batch: continue
        
        start_num = extract_ep_num(batch[0])
        end_num = extract_ep_num(batch[-1])
        
        if len(batch) == 1:
            batch_label = f"Eps {start_num}"
        else:
            batch_label = f"Eps {start_num}-{end_num}"
            
        out_name = f"{DRAMA_TITLE} - {batch_label}.mp4"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        
        if os.path.exists(out_path):
            print(f"  [SKIP] {out_name} sudah ada.")
            continue
            
        t0 = time.time()
        ok = process_and_merge(batch, batch_label, out_path)
        if ok:
            print(f"    -> SELESAI ({time.time() - t0:.1f} detik): {out_name}")
        else:
            print(f"    -> GAGAL memproses {batch_label}")

if __name__ == "__main__":
    main()
