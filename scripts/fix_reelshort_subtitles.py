import requests
import boto3
import re
import sys
import urllib.parse
from botocore.config import Config

API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

WEB_HDRS    = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://vidrama.asia/',
}

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def slugify(text):
    text = text.lower()
    return re.sub(r'[\W_]+', '-', text).strip('-')

def fix_drama_subtitles(movie_id):
    r2 = get_r2()
    
    url = f"https://vidrama.asia/api/reelshort/detail?id={movie_id}&lang=in"
    r = requests.get(url, headers=WEB_HDRS, verify=False).json()
    detail = r.get('detail', {})
    title = detail.get('title')
    total_eps = detail.get('chapters', 0)
    slug = slugify(title)
    prefix = f"reelshort/{slug}"
    
    print(f"Fixing subtitles for: {title} ({total_eps} episodes)")
    
    # Get DB ID
    r_search = requests.get(f"{API_BASE}/dramas/search?q={title}").json().get('dramas', [])
    db_id = None
    for d in r_search:
        if d['title'].lower().strip() == title.lower().strip():
            db_id = d['id']
            break
            
    if not db_id:
        print("Drama not found in DB!")
        return
        
    print(f"DB ID: {db_id}")
    
    # Get all episodes from DB
    db_eps_req = requests.get(f"{API_BASE}/dramas/{db_id}").json()
    db_eps = {ep['episodeNumber']: ep['id'] for ep in db_eps_req.get('episodes', [])}
    
    for ep_no in range(1, total_eps + 1):
        print(f"  ep{ep_no:03d}... ", end="")
        
        ep_id = db_eps.get(ep_no)
        if not ep_id:
            print("Not in DB, skipping.")
            continue
            
        ksub = f"{prefix}/ep{ep_no:03d}.vtt"
        
        # Check if already exists in DB
        ep_detail = requests.get(f"{API_BASE}/admin/episodes/{ep_id}", headers=ADMIN_HDR).json()
        if any(s.get('language') == 'indonesia' for s in ep_detail.get('subtitles', [])):
            print("Subtitle already linked in DB.")
            continue
            
        # Fetch subtitle URL
        vid_url = f"https://vidrama.asia/api/reelshort/video?bookId={movie_id}&episode={ep_no}"
        v_res = requests.get(vid_url, headers=WEB_HDRS, verify=False).json()
        subtitles = v_res.get('subtitles', [])
        
        id_sub_url = None
        for s in subtitles:
            if s.get('language', '').lower() in ['in', 'id', 'id-id']:
                id_sub_url = s.get('url')
                if id_sub_url and id_sub_url.startswith('/'):
                    id_sub_url = f"https://vidrama.asia{id_sub_url}"
                break
                
        if not id_sub_url:
            print("No Indo subtitle found.")
            continue
            
        try:
            sub_res = requests.get(id_sub_url, headers=WEB_HDRS, verify=False)
            content = sub_res.content.decode('utf-8', errors='ignore')
            content = re.sub(r'font-size\s*:\s*\d+(?:\.\d+)?%?\s*;?', '', content, flags=re.IGNORECASE)
            
            r2.put_object(Bucket=R2_BUCKET, Key=ksub, Body=content.encode('utf-8'), ContentType='text/vtt')
            final_sub_r2 = f"{R2_PUBLIC}/{ksub}"
            
            sub_payload = {'language': 'indonesia', 'label': 'Indonesia', 'url': final_sub_r2, 'isDefault': True}
            r_post = requests.post(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload)
            if r_post.ok:
                print("Uploaded & Linked!")
            else:
                print("Failed to link DB.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        fix_drama_subtitles(sys.argv[1])
