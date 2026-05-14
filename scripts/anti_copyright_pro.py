import os
import subprocess
import json

def get_media_info(file_path):
    """Mendapatkan resolusi video dan sample rate audio menggunakan ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_streams', file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        info = json.loads(result.stdout)
        
        width = 1080
        height = 1920
        sample_rate = 44100
        
        for stream in info.get('streams', []):
            if stream['codec_type'] == 'video':
                width = int(stream['width'])
                height = int(stream['height'])
            elif stream['codec_type'] == 'audio':
                sample_rate = int(stream['sample_rate'])
                
        return width, height, sample_rate
    except Exception as e:
        print(f"Gagal membaca info {file_path}. Menggunakan nilai default.")
        return 1080, 1920, 44100

def process_videos_pro(input_folder):
    """Memproses video dan audio secara bersamaan (Re-encode) untuk bypass hak cipta visual."""
    output_folder = os.path.join(input_folder, "Aman_Copyright_Pro")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    files = [f for f in os.listdir(input_folder) if f.endswith(".mp4") and f.startswith("Part_")]
    
    if not files:
        print(f"Tidak ditemukan file berawalan 'Part_' di {input_folder}")
        return

    print(f"Ditemukan {len(files)} video.")
    print("Memulai proses bypass hak cipta VISUAL & AUDIO (Proses ini akan memakan waktu)...")

    for filename in files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        
        print(f"\n[+] Memproses: {filename}")
        
        # 1. Ambil info video asli
        w, h, sr = get_media_info(input_path)
        
        # 2. Hitung Crop (Potong 6% dari pinggiran video untuk merusak sidik jari visual)
        crop_w = int(w * 0.94)
        crop_h = int(h * 0.94)
        # Pastikan genap (ffmpeg butuh angka genap untuk resolusi)
        crop_w = crop_w - (crop_w % 2)
        crop_h = crop_h - (crop_h % 2)
        
        # 3. Filter Visual (Video) Ajaib:
        # - setpts=PTS/1.05 : Mempercepat video 5%
        # - crop & scale : Memotong sedikit tepi video lalu membesarkannya lagi ke ukuran asli (Zomming)
        # - eq : Menambahkan sedikit pencerahan (brightness) dan saturasi
        video_filter = f"setpts=PTS/1.05,crop={crop_w}:{crop_h},scale={w}:{h},eq=brightness=0.02:saturation=1.05:contrast=1.02"
        
        # 4. Filter Audio Ajaib:
        # - asetrate : Menaikkan pitch dan kecepatan 5% (sehingga pas dan sinkron dengan video yang dicepatkan)
        # - aresample : Mengembalikan standar sample rate
        new_sr = int(sr * 1.05)
        audio_filter = f"asetrate={new_sr},aresample={sr}"
        
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-vf', video_filter,
            '-af', audio_filter,
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '26', # Render video (veryfast agar tidak menunggu lama)
            '-c:a', 'aac', '-b:a', '128k', # Render audio
            output_path
        ]
        
        print(f"    -> Sedang merender (Harap tunggu, proses ini butuh kinerja CPU)...")
        subprocess.run(cmd)
        print(f"    -> Selesai: {filename}")

if __name__ == "__main__":
    # Target Folder Anda
    folder_target = r"D:\Video Drama\Tebus_Langit"
    process_videos_pro(folder_target)
    print("\n=======================================================")
    print("[SUKSES] Semua video telah berhasil di-render ulang secara penuh.")
    print(f"Hasil video versi kebal hak cipta ada di: {os.path.join(folder_target, 'Aman_Copyright_Pro')}")
    print("=======================================================")
