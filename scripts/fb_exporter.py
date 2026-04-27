import os, re, subprocess, shutil
import boto3
from dotenv import load_dotenv

load_dotenv(r'd:\kingshortid\scripts\melolo-scraper\.env')

s3 = boto3.client('s3', 
    endpoint_url=os.getenv('R2_ENDPOINT'), 
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'), 
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY')
)

BUCKET = 'shortlovers'
BASE_DIR = r'D:\Video Drama'

DRAMAS = [
    {"title": "Dokter Ajaib Dari Desa", "prefix": "melolo/dokter-ajaib-dari-desa/"},
    {"title": "Aku Kaya Dari Giok", "prefix": "melolo/aku-kaya-dari-giok/"},
    {"title": "Raja Tinju di Balik Gerobak", "prefix": "dramas/netshort/raja-tinju-di-balik-gerobak/"},
    {"title": "(Sulih Suara) Kebangkitan Raja Balap", "prefix": "dramas/netshort/sulih-suara-kebangkitan-raja-balap/"},
    {"title": "Aku Sungguh Bukan Dewa", "prefix": "dramas/microdrama/aku-sungguh-bukan-dewa/"}
]

def download_file(key, dest):
    print(f"  Downloading: {key.split('/')[-1]}")
    s3.download_file(BUCKET, key, dest)

def merge_videos(vid1, vid2, output, list_txt):
    with open(list_txt, 'w', encoding='utf-8') as f:
        # ffmpeg requires forward slashes or escaped backslashes for paths in concat file
        f.write(f"file '{vid1.replace(chr(92), '/')}'\n")
        f.write(f"file '{vid2.replace(chr(92), '/')}'\n")
    
    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_txt, '-c', 'copy', output]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def process_drama(drama):
    title = drama['title']
    prefix = drama['prefix']
    
    drama_dir = os.path.join(BASE_DIR, title)
    temp_dir = os.path.join(drama_dir, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    print(f"\n======================================")
    print(f"Processing: {title}")
    
    # 1. List objects
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=BUCKET, Prefix=prefix)
    
    episodes = {}
    cover_key = None
    
    for page in pages:
        for obj in page.get('Contents', []):
            key = obj['Key']
            filename = key.split('/')[-1]
            if '540p' in filename:
                continue
            
            if filename.startswith('cover.') or filename.startswith('poster.'):
                cover_key = key
            
            match = re.search(r'ep(\d+)\.mp4', filename)
            if match:
                ep_num = int(match.group(1))
                episodes[ep_num] = key
                
    if cover_key:
        cover_ext = cover_key.split('.')[-1]
        cover_dest = os.path.join(drama_dir, f"Cover.{cover_ext}")
        if not os.path.exists(cover_dest):
            download_file(cover_key, cover_dest)
            
    ep_nums = sorted(episodes.keys())
    print(f"Found {len(ep_nums)} episodes.")
    
    for i in range(0, len(ep_nums), 2):
        ep1_num = ep_nums[i]
        ep1_key = episodes[ep1_num]
        
        # Check if we have a pair
        if i + 1 < len(ep_nums):
            ep2_num = ep_nums[i+1]
            ep2_key = episodes[ep2_num]
            out_name = f"Eps {ep1_num}-{ep2_num}.mp4"
            out_path = os.path.join(drama_dir, out_name)
            
            if os.path.exists(out_path):
                print(f"  [SKIP] {out_name} already exists.")
                continue
                
            vid1 = os.path.join(temp_dir, f"ep{ep1_num}.mp4")
            vid2 = os.path.join(temp_dir, f"ep{ep2_num}.mp4")
            list_txt = os.path.join(temp_dir, 'list.txt')
            
            download_file(ep1_key, vid1)
            download_file(ep2_key, vid2)
            
            print(f"  Merging to: {out_name}")
            merge_videos(vid1, vid2, out_path, list_txt)
            
            # Clean temp
            try: os.remove(vid1); os.remove(vid2); os.remove(list_txt)
            except: pass
        else:
            # Single episode (odd count, last one)
            out_name = f"Eps {ep1_num}.mp4"
            out_path = os.path.join(drama_dir, out_name)
            if os.path.exists(out_path):
                print(f"  [SKIP] {out_name} already exists.")
                continue
            
            print(f"  Copying single: {out_name}")
            download_file(ep1_key, out_path)

    # Clean temp dir completely
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"Finished: {title}")

if __name__ == '__main__':
    for d in DRAMAS:
        process_drama(d)
    print("\nALL DONE!")
