import re

with open('scripts/scrape_melolov3_provider.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the comments and prefix
content = content.replace('melolov3 Provider', 'idrama2 Provider')
content = content.replace('melolov3/', 'idrama2/')

# 2. Update the API URL logic in scrape_single_drama
api_fetch_old = """    # 1. Fetch details from API
    url = f"https://vidrama.asia/api/melolov3/multi-video?id={movie_id}&lang=id"
    print(f"Fetching details from API: {url}")
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        if not r.ok:
            print(f"[ERROR] Failed to fetch drama details. Status: {r.status_code}")
            return False
        res_json = r.json()
        detail = res_json.get('series', {})
        eps = res_json.get('episodes', [])
    except Exception as e:
        print(f"[ERROR] Exception fetching drama details: {e}")
        return False
        
    title = detail.get('title') or 'Unknown Title'
    
    # We must remap detail to match api_get_or_create_drama format expected from melolov2
    detail_remapped = {
        'title': title,
        'description': detail.get('intro'),
        'cover': detail.get('cover'),
        'chapterCount': detail.get('episode_count'),
        'bookStatus': 1 # Assume completed if episodes are available
    }"""

api_fetch_new = """    # 1. Fetch details from API
    url = f"https://vidrama.asia/api/idrama2/drama/{movie_id}?lang=id"
    print(f"Fetching details from API: {url}")
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        if not r.ok:
            print(f"[ERROR] Failed to fetch drama details. Status: {r.status_code}")
            return False
        res_json = r.json()
        detail = res_json
        eps = res_json.get('episode_list', [])
    except Exception as e:
        print(f"[ERROR] Exception fetching drama details: {e}")
        return False
        
    title = detail.get('short_play_name') or 'Unknown Title'
    
    detail_remapped = {
        'title': title,
        'description': detail.get('introduction'),
        'cover': detail.get('cover_url') or detail.get('compress_cover_url'),
        'chapterCount': detail.get('current_count'),
        'bookStatus': 1
    }"""
content = content.replace(api_fetch_old, api_fetch_new)

# 3. Fix cover URL extraction
cover_upload_old = """                    cover_src = detail.get('cover')"""
cover_upload_new = """                    cover_src = detail.get('cover_url') or detail.get('compress_cover_url')"""
content = content.replace(cover_upload_old, cover_upload_new)

# 4. Fix episode extraction
ep_loop_old = """            ep_no = ep.get('index')
            if ep_no is None:
                continue
                
            k720 = f"{prefix}/ep{ep_no:03d}.mp4"
            k540 = f"{prefix}/ep{ep_no:03d}_540p.mp4"
            ksub = f"{prefix}/ep{ep_no:03d}.vtt"
            
            # If both 720p and 540p exist in R2, skip download/transcode
            if r2_exists(r2, k720) and r2_exists(r2, k540):"""

ep_loop_new = """            ep_no = ep.get('episode_order')
            if ep_no is None:
                continue
                
            k720 = f"{prefix}/ep{ep_no:03d}.mp4"
            k540 = f"{prefix}/ep{ep_no:03d}_540p.mp4"
            ksub = f"{prefix}/ep{ep_no:03d}.vtt"
            
            # If both 720p and 540p exist in R2, skip download/transcode
            if r2_exists(r2, k720) and r2_exists(r2, k540):"""
content = content.replace(ep_loop_old, ep_loop_new)

vurl_old = """            # Stream URL is directly available in the episode object from multi-video API
            vurl = ep.get('stream_url')
            subtitles = ep.get('subtitles', [])"""
vurl_new = """            # Stream URL and subtitles
            vurl = None
            for p in ep.get('play_info_list', []):
                if p.get('definition') in ['720p', '1080p', '540p']:
                    if p.get('play_url'):
                        vurl = p.get('play_url')
                        if p.get('definition') == '720p':
                            break
                            
            subtitles = ep.get('subtitle_list', []) + ep.get('screentext_list', [])"""
content = content.replace(vurl_old, vurl_new)

with open('scripts/scrape_idrama2_provider.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Modification complete.")
