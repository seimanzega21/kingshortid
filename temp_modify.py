import re, os

with open('scripts/scrape_custom_fb.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Modify process_episode_sop signature and logic to copy local file
content = content.replace(
    'def process_episode_sop(ep_data, drama_id, slug, r2, provider):',
    'def process_episode_sop(ep_data, drama_id, slug, r2, provider, local_dir):'
)

copy_logic = """        f_540 = out_540 if os.path.exists(out_540) else out_raw
        with open(f_540, 'rb') as f:
            r2.upload_fileobj(f, BUCKET, key_540, ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})
            
        # --- LOCAL COPY LOGIC ---
        if local_dir:
            import shutil
            local_ep_path = os.path.join(local_dir, f"ep{ep_no:02d}.mp4")
            shutil.copy2(out_raw, local_ep_path)
"""
content = content.replace(
    """        f_540 = out_540 if os.path.exists(out_540) else out_raw
        with open(f_540, 'rb') as f:
            r2.upload_fileobj(f, BUCKET, key_540, ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})""",
    copy_logic
)

# 2. Update ThreadPoolExecutor call
content = content.replace(
    '{executor.submit(process_episode_sop, ep, drama_db_id, slug, r2, provider): ep for ep in missing_eps}',
    '{executor.submit(process_episode_sop, ep, drama_db_id, slug, r2, provider, local_dir): ep for ep in missing_eps}'
)

# 3. Modify cover conversion to upscale and save locally
cover_logic_old = """                    subprocess.run(['ffmpeg', '-y', '-i', raw_cov, '-update', '1', '-q:v', '2', jpg_cov], check=True, capture_output=True)
                    with open(jpg_cov, "rb") as f:
                        r2.upload_fileobj(f, BUCKET, f"{provider}/{slug}/cover_hq.jpg", ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'})"""

cover_logic_new = """                    # Upscale cover to 1080p width to make it HD
                    subprocess.run(['ffmpeg', '-y', '-i', raw_cov, '-vf', 'scale=1080:-1', '-update', '1', '-q:v', '2', jpg_cov], check=True, capture_output=True)
                    with open(jpg_cov, "rb") as f:
                        r2.upload_fileobj(f, BUCKET, f"{provider}/{slug}/cover_hq.jpg", ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'})
                    
                    if local_dir:
                        import shutil
                        local_cov_path = os.path.join(local_dir, "cover_hq.jpg")
                        shutil.copy2(jpg_cov, local_cov_path)
"""
content = content.replace(cover_logic_old, cover_logic_new)

# 4. Add local_dir logic to process_single_drama
content = content.replace(
    'def process_single_drama(drama_info, provider, is_dry_run):',
    'def process_single_drama(drama_info, provider, is_dry_run, local_base_dir):'
)

local_dir_setup = """
    if local_base_dir:
        import re
        safe_title = re.sub(r'[\\\\/*?:"<>|]', "", title)
        local_dir = os.path.join(local_base_dir, safe_title)
        os.makedirs(local_dir, exist_ok=True)
    else:
        local_dir = None
        
    print(f"   [*] Ditemukan {len(episodes)} episode di sumbernya.")
"""
content = content.replace('    print(f"   [*] Ditemukan {len(episodes)} episode di sumbernya.")', local_dir_setup)


# 5. Replace main function
new_main = """
def main():
    urls = [
        "https://vidrama.asia/movie/traktor-pembawa-harta-1--7684191755922623493?provider=melolov3&lang=id",
        "https://vidrama.asia/movie/ayah-bangkrut-jadi-nelayan--7681995902046702645?provider=melolov3&lang=id",
        "https://vidrama.asia/movie/semua-kakakku-penguasa-dunia-kultivasi--7686450865250683957?provider=melolov3&lang=id",
        "https://vidrama.asia/movie/hidup-kembali-tak-kejar-dia--7686761968975268869?provider=melolov3&lang=id",
        "https://vidrama.asia/movie/petualangan-istri-asing-1--7684828423423806517?provider=melolov3&lang=id",
        "https://vidrama.asia/movie/si-miskin-di-puncak-2--7688607632566799365?provider=melolov3&lang=id",
        "https://vidrama.asia/movie/lima-kakak-perkasa-2--7683786605877791797?provider=melolov3&lang=id",
        "https://vidrama.asia/movie/berburu-demi-adik-1--7684827819897015349?provider=melolov3&lang=id",
        "https://vidrama.asia/movie/membangun-sekte-abadi-sang-kaisar--7684546976163073029?provider=melolov3&lang=id",
        "https://vidrama.asia/movie/taktik-modern-di-era-kuno-2--7680466037573176373?provider=melolov3&lang=id"
    ]
    local_base_dir = r"D:\\Video Drama\\Facebook\\Terbaru"
    os.makedirs(local_base_dir, exist_ok=True)
    
    print("="*70)
    print(f"CUSTOM SCRAPER PIPELINE - 10 Dramas")
    print("="*70)
    
    for url in urls:
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        path_parts = parsed.path.split('/')
        vid_id = path_parts[-1].split('--')[-1]
        slug = path_parts[-1].split('--')[0]
        
        # Format the title nicely from slug
        title = slug.replace('-', ' ').title()
        
        qs = urllib.parse.parse_qs(parsed.query)
        provider = qs.get('provider', ['melolo'])[0]
        
        drama_info = {
            'id': vid_id,
            'slug': slug,
            'title': title,
            'genres': ['Drama']
        }
        
        # Get genres from vidrama API
        import requests
        try:
            r = requests.get(f"https://vidrama.asia/api/{provider}/series?id={vid_id}&lang=id", headers=WEB_HDRS, verify=False, timeout=10)
            if r.ok:
                d_json = r.json()
                cats = d_json.get('series', {}).get('category', [])
                if cats:
                    drama_info['genres'] = [c.get('name') for c in cats if c.get('name')]
        except Exception as e:
            print("Failed to fetch genres, using defaults")
            
        process_single_drama(drama_info, provider, False, local_base_dir)

if __name__ == '__main__':
    main()
"""

main_idx = content.find('def main():')
content = content[:main_idx] + new_main

with open('scripts/scrape_custom_fb.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Modified scrape_custom_fb.py successfully!")
