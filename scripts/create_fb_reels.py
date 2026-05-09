import os, subprocess, requests, boto3, tempfile
from pathlib import Path
from botocore.config import Config

# --- KONFIGURASI R2 ---
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

# Daftar 7 Judul yang diminta
TARGETS = [
    {'slug': 'penebusan-sang-tabib', 'title': 'Penebusan Sang Tabib'},
    {'slug': 'istri-pewaris-yang-ditakuti', 'title': 'Istri Pewaris Yang Ditakuti'},
    {'slug': 'dewa-biliar', 'title': 'Dewa Biliar'},
    {'slug': 'tebus-langit', 'title': 'Tebus Langit'},
    {'slug': 'jangan-kira-dia-polos', 'title': 'Jangan Kira Dia Polos'},
    {'slug': 'menghabisi-yang-jahat', 'title': 'Menghabisi Yang Jahat'},
    {'slug': 'penjahat-nomor-satu', 'title': 'Penjahat Nomor Satu'}
]

OUTPUT_DIR = Path(r"D:\Video Drama")

def get_r2_keys(prefix):
    r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                      aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                      config=Config(signature_version='s3v4'), region_name='auto')
    keys = []
    paginator = r2.get_paginator('list_objects_v2')
    try:
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix):
            for obj in page.get('Contents', []):
                keys.append(obj['Key'])
    except Exception as e:
        print(f"Error list R2: {e}")
    return keys

def download_file(url, dest):
    if dest.exists() and dest.stat().st_size > 1000:
        return True
    try:
        with requests.get(url, stream=True, timeout=15) as r:
            if r.status_code == 200:
                with open(dest, 'wb') as f:
                    for chunk in r.iter_content(2*1024*1024):
                        if chunk: f.write(chunk)
                return True
    except: pass
    if dest.exists(): dest.unlink()
    return False

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("🎬 PEMBUAT KONTEN FACEBOOK REELS/TIKTOK (3-IN-1) DIMULAI")
    print("="*60)
    
    for target in TARGETS:
        slug = target['slug']
        title = target['title']
        title_safe = title.replace(' ', '_').replace(':', '')
        
        target_dir = OUTPUT_DIR / title_safe
        target_dir.mkdir(exist_ok=True)
        raw_dir = target_dir / "Raw"
        raw_dir.mkdir(exist_ok=True)
        
        print(f"\n======================================")
        print(f"🎬 MEMPROSES: {title}")
        print(f"======================================")
        
        prefix = f"netshortv2/{slug}/"
        print("-> Memeriksa file di R2...")
        keys = get_r2_keys(prefix)
        
        # Kumpulkan episode (hanya file epXXX.mp4)
        ep_numbers = []
        for k in keys:
            if k.endswith('.mp4') and '540p' not in k and 'subbed' not in k:
                # ekstrak nomor episode dari "ep001.mp4"
                name = k.split('/')[-1]
                if name.startswith('ep') and name.endswith('.mp4'):
                    try:
                        num = int(name[2:5])
                        ep_numbers.append(num)
                    except: pass
                    
        ep_numbers = sorted(list(set(ep_numbers)))
        if not ep_numbers:
            print("   TIDAK ADA EPISODE DITEMUKAN!")
            continue
            
        print(f"-> Ditemukan {len(ep_numbers)} episode. Mulai mengunduh & render subtitle...")
        
        subbed_files = []
        for ep in ep_numbers:
            mp4_url = f"{R2_PUBLIC}/{prefix}ep{ep:03d}.mp4"
            vtt_url = f"{R2_PUBLIC}/{prefix}ep{ep:03d}.vtt"
            
            raw_mp4 = raw_dir / f"ep_{ep:03d}.mp4"
            raw_vtt = raw_dir / f"ep_{ep:03d}.vtt"
            subbed_mp4 = raw_dir / f"ep_{ep:03d}_subbed.mp4"
            
            # Download MP4
            if not raw_mp4.exists():
                print(f"  -> [Unduh] Ep {ep}...", end="", flush=True)
                success = download_file(mp4_url, raw_mp4)
                print(" OK" if success else " GAGAL")
                if not success: continue
                
            # Download VTT (optional)
            if not raw_vtt.exists():
                download_file(vtt_url, raw_vtt)
                
            # Burn Subtitles
            if not subbed_mp4.exists() and raw_mp4.exists():
                print(f"  -> [Render Sub] Ep {ep}...", end="", flush=True)
                
                # SETTING SUBTITLE UNTUK FACEBOOK REELS:
                # Alignment=2 (Bawah-Tengah), MarginV=350 (Naik ke tengah layar), Fontsize=22 (Ukuran proporsional)
                style = "Alignment=2,MarginV=350,Fontname=Arial,Fontsize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,Bold=-1"
                
                if raw_vtt.exists():
                    vtt_filename = f"ep_{ep:03d}.vtt"
                    # Escape karakter titik dua (:) pada drive Windows jika tidak menggunakan CWD
                    vf = f"subtitles={vtt_filename}:force_style='{style}'"
                else:
                    vf = "scale=iw:ih"
                    
                cmd = [
                    "ffmpeg", "-y", "-i", f"ep_{ep:03d}.mp4",
                    "-vf", vf,
                    "-c:v", "libx264", "-crf", "26", "-preset", "fast",
                    "-c:a", "copy",
                    f"ep_{ep:03d}_subbed.mp4"
                ]
                
                res = subprocess.run(cmd, cwd=str(raw_dir), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    print(" SELESAI")
                else:
                    print(" ERROR ENCODING")
                    
            if subbed_mp4.exists():
                subbed_files.append(subbed_mp4)
                
        # GABUNGKAN PER 3 EPISODE
        print(f"\n-> Menggabungkan {len(subbed_files)} episode menjadi Part 3-in-1...")
        batch_size = 3
        part_no = 1
        for i in range(0, len(subbed_files), batch_size):
            chunk = subbed_files[i:i+batch_size]
            if not chunk: continue
            
            # Hitung nomor episode awal dan akhir di chunk ini
            # ekstrak dari nama file ep_001_subbed.mp4
            try:
                start_ep = int(chunk[0].name.split('_')[1])
                end_ep = int(chunk[-1].name.split('_')[1])
            except:
                start_ep = i + 1
                end_ep = i + len(chunk)
                
            part_filename = target_dir / f"Part_{part_no:02d}_(Eps_{start_ep}-{end_ep}).mp4"
            if part_filename.exists():
                print(f"  -> {part_filename.name} SUDAH ADA. Melewati...")
                part_no += 1
                continue
                
            print(f"  -> Membuat {part_filename.name}...", end="", flush=True)
            
            list_txt = raw_dir / "concat_list.txt"
            with open(list_txt, "w") as f:
                for sf in chunk:
                    f.write(f"file '{sf.name}'\n")
                    
            cmd_concat = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", "concat_list.txt",
                "-c", "copy",
                str(part_filename.absolute())
            ]
            
            res = subprocess.run(cmd_concat, cwd=str(raw_dir), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                print(" BERHASIL")
            else:
                print(" GAGAL")
                
            part_no += 1
            
    print("\n" + "="*60)
    print("🎉 SELURUH PROSES PEMBUATAN VIDEO FACEBOOK SELESAI!")
    print("Video hasil gabungan siap diposting di folder D:\Video Drama")

if __name__ == "__main__":
    main()
