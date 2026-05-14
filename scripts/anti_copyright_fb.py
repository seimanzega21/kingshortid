import os
import subprocess
import json

def get_sample_rate(file_path):
    """Mendapatkan sample rate audio asli menggunakan ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_streams', '-select_streams', 'a:0', file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        info = json.loads(result.stdout)
        sample_rate = info['streams'][0]['sample_rate']
        return int(sample_rate)
    except Exception as e:
        print(f"Gagal membaca sample rate dari {file_path}. Menggunakan default 44100.")
        return 44100

def process_videos(input_folder):
    """Memproses semua video di folder untuk bypass hak cipta audio."""
    # Buat folder output
    output_folder = os.path.join(input_folder, "Aman_Copyright")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Ambil semua file Part_*.mp4
    files = [f for f in os.listdir(input_folder) if f.endswith(".mp4") and f.startswith("Part_")]
    
    if not files:
        print(f"Tidak ditemukan file berawalan 'Part_' di {input_folder}")
        return

    print(f"Ditemukan {len(files)} video. Memulai proses bypass hak cipta...")

    for filename in files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        
        print(f"\nMemproses: {filename}")
        
        # 1. Dapatkan sample rate asli (biasanya 44100 atau 48000)
        sr = get_sample_rate(input_path)
        
        # 2. Kita naikkan pitch sebesar 6% (sekitar 1 semitone)
        new_sr = int(sr * 1.06) 
        
        # Penjelasan Filter Audio Ajaib:
        # - asetrate: Memaksa audio diputar lebih cepat (pitch naik 6%, durasi lebih pendek)
        # - aresample: Mengembalikan format ke sample rate standar
        # - atempo: Memperlambat kembali durasi audio ke normal (pitch tetap naik, durasi kembali pas dengan video!)
        audio_filter = f"asetrate={new_sr},aresample={sr},atempo=1/1.06"
        
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-c:v', 'copy',                # COPY VIDEO (Sangat Cepat, tidak render ulang gambar!)
            '-af', audio_filter,           # Terapkan filter audio
            '-c:a', 'aac', '-b:a', '128k', # Render ulang ke AAC
            output_path
        ]
        
        # Jalankan FFmpeg
        subprocess.run(cmd)
        print(f"Selesai: {output_path} -> Disimpan di folder Aman_Copyright")

if __name__ == "__main__":
    # Target Folder Anda
    folder_target = r"D:\Video Drama\Tebus_Langit"
    process_videos(folder_target)
    print("\n=======================================================")
    print("[SUKSES] Semua video telah diproses dengan trik anti-copyright.")
    print(f"Silakan periksa hasilnya di: {os.path.join(folder_target, 'Aman_Copyright')}")
    print("=======================================================")
