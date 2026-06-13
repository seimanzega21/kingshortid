# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import boto3
import time
import re
import warnings
warnings.filterwarnings('ignore')
from botocore.config import Config

# R2 Configuration
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
}

dramas = [
    {
        'name': 'Istriku Bisa Bunuh Dewa',
        'upstream_id': '160000641572',
        'slug': 'istriku-bisa-bunuh-dewa',
        'total_eps': 70
    },
    {
        'name': 'Aku Terlahir Terlalu Patuh',
        'upstream_id': '160000641860',
        'slug': 'aku-terlahir-terlalu-patuh',
        'total_eps': 75
    }
]

def log(msg):
    ts = time.strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def srt_to_vtt(srt_text):
    if srt_text.strip().startswith('WEBVTT'):
        return srt_text
    lines = srt_text.splitlines()
    vtt_lines = ['WEBVTT', '']
    timestamp_re = re.compile(r'(\d{2}:\d{2}:\d{2}),(\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}),(\d{3})')
    for line in lines:
        match = timestamp_re.search(line)
        if match:
            formatted_line = line.replace(',', '.')
            vtt_lines.append(formatted_line)
        else:
            vtt_lines.append(line)
    return '\n'.join(vtt_lines)

def patch_subtitle(r2, upstream_id, ep_no, slug):
    url = f"https://vidrama.asia/api/idrama2/unlock/{upstream_id}/{ep_no}?lang=id"
    for attempt in range(5):
        try:
            resp = requests.get(url, headers=HEADERS, verify=False, timeout=15)
            if resp.ok:
                data = resp.json().get('target_ep_info', {})
                # Try subtitle_list first
                sub_url = None
                sub_list = data.get('subtitle_list') or []
                for s in sub_list:
                    if s.get('language', '').lower() == 'id' and s.get('url'):
                        sub_url = s['url']
                        break
                
                # Fallback to screentext_list
                if not sub_url:
                    screen_list = data.get('screentext_list') or []
                    for s in screen_list:
                        if s.get('language', '').lower() == 'id' and s.get('url'):
                            sub_url = s['url']
                            break
                
                if not sub_url:
                    log(f"    EP {ep_no}: No Indonesian subtitle URL found.")
                    return False
                
                # Download subtitle
                sub_resp = requests.get(sub_url, headers=HEADERS, verify=False, timeout=15)
                if sub_resp.ok:
                    sub_text = sub_resp.text
                    if not sub_text.strip().startswith('WEBVTT'):
                        sub_text = srt_to_vtt(sub_text)
                    
                    sub_key = f"dramas/{slug}/ep{ep_no:03d}_id.vtt"
                    r2.put_object(Bucket=R2_BUCKET, Key=sub_key, Body=sub_text.encode('utf-8'), ContentType='text/vtt')
                    return True
            time.sleep(2)
        except Exception as e:
            log(f"    EP {ep_no} attempt {attempt+1} error: {e}")
            time.sleep(2)
    return False

def main():
    r2 = get_r2()
    for d in dramas:
        log("=" * 60)
        log(f"PATCHING: {d['name']} (Slug: {d['slug']})")
        log("=" * 60)
        
        success = 0
        failed = []
        for ep in range(1, d['total_eps'] + 1):
            ok = patch_subtitle(r2, d['upstream_id'], ep, d['slug'])
            if ok:
                success += 1
                if ep % 10 == 0 or ep == d['total_eps']:
                    log(f"  Processed ep {ep}/{d['total_eps']}... (success count: {success})")
            else:
                log(f"  [FAILED] ep {ep}")
                failed.append(ep)
            time.sleep(0.3)
            
        log(f"Completed {d['name']}. Success: {success}/{d['total_eps']}")
        if failed:
            log(f"Failed eps: {failed}")

if __name__ == '__main__':
    main()
