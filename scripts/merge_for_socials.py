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
    Menggabungkan menggunakan concat filter (BUKAN concat demuxer) untuk memastikan 
    sinkronisasi Audio dan Subtitle/Video 100% presisi. VFR (Variable Frame Rate) akan 
    diperbaiki secara otomatis oleh filter ini.
    """
    print(f"  Memproses {batch_label} ...")
    intro_path = os.path.join(TEMP_DIR, f"intro_{batch_label}.mp4")
    
    if not create_title_intro(batch_label, intro_path):
        print(f"    [!] Gagal membuat intro untuk {batch_label}")
        return False
        
    cmd = [
        "ffmpeg", "-y",
        "-i", intro_path
    ]
    
    for ep in batch_files:
        cmd.extend(["-i", ep])
        
    filter_complex = "[0:v]setsar=1:1,fps=30[v0];"
    concat_inputs = "[v0][0:a]"
    
    # Filter bypass HANYA menggunakan Crop + Color Shift + Strip Metadata.
    # Speedup dihapus karena memicu masalah sinkronisasi subtitle pada video VFR Tiongkok.
    for i in range(1, len(batch_files) + 1):
        filter_complex += f"[{i}:v]crop=iw*0.98:ih*0.98,scale=720:1280,setsar=1:1,eq=brightness=0.01:contrast=1.02:saturation=1.05,fps=30[v{i}];"
        filter_complex += f"[{i}:a]aresample=44100[a{i}];"
        concat_inputs += f"[v{i}][a{i}]"
        
    n_total = len(batch_files) + 1
    filter_complex += f"{concat_inputs}concat=n={n_total}:v=1:a=1[vout][aout]"
    
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-map_metadata", "-1",
        "-c:v", "libx264", "-preset", "fast", "-crf", "26",
        "-c:a", "aac", "-b:a", "128k",
        "-async", "1",
        "-movflags", "+faststart",
        output_path
    ])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if result.returncode != 0:
            print(f"    [!] FFmpeg Gagal, Error Log:\n{result.stderr}")
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
    
    logical_ep = 1
    
    for i in range(0, total_eps, EPISODES_PER_BATCH):
        batch = episodes[i:i+EPISODES_PER_BATCH]
        if not batch: continue
        
        start_num = logical_ep
        end_num = logical_ep + len(batch) - 1
        
        logical_ep += len(batch)
        
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
