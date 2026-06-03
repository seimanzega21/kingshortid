# -*- coding: utf-8 -*-
"""
Backfill Script for "Janji Kuno (Sulih Suara)"
Scrapes missing episodes: 26 to 35
Directly streams to R2 & registers to database
"""
import requests
import boto3
import sys
import json
import time
import io
import urllib3
from botocore.config import Config

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

# ─── CONFIG ─────────────────────────────────────────────────────────────────
BOOK_ID = '42000007062'
BOOK_SLUG = 'janji-kuno-sulih-suara'
DRAMA_ID = 'pjr00rw58d0y73bk7axn1buy'
START_EP = 26
END_EP = 35

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET = 'shortlovers'
R2_PUBLIC = 'https://stream.shortlovers.id'

COOKIE = '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCnv5004644=48; cf_clearance=N5A.kyHMnJ7RBK3hOyqybB6KddOTpRsZyEiE.fgp5kM-1779713242-1.2.1.1-9YHMfsNOniF6J54T1_JEaJY6mYbVJWOz8Kkm0raJacrpotGOYzyN_gG.Kxb7kfPxOO1wYdSenqFW0HIUwqQ57F5gqyjRbwvS8_r8rLFxIbYHNWMAahrr.iKy0dsa1krg8mVhzXDilHK71X.Iszvd8uo_CwVzbHiVUurJ8eF1DyguF2fK1vFa68H3Z5HFzZhBvVaIle1tEW3443.tH9TYjQX.7HKB9SBI2ZHkNto2vDQ2F77XP3cLmCp7GPXINCG8mrZf6l5xsxuh_xyqNp1bIRyxkUhz9IooxQKp3yV9Crri9TFW9II5q0M50yOlhCROGsKwa0AkIkKtWi.pNc5ATg; HstCla5004644=1779713242621; HstPn5004644=2; HstPt5004644=93; HstCns5004644=54; panoramaId_expiry=1779799644224'

VIDRAMA_HDR = {
    'accept': '*/*',
    'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'cookie': COOKIE,
    'priority': 'u=1, i',
    'referer': f'https://vidrama.asia/watch/janji-kuno--{BOOK_ID}/26?provider=dramabox3&lang=in',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36'
}

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def get_episode_data(ep_no):
    """Get stream URLs + subtitles for an episode"""
    url = f'https://vidrama.asia/api/dramabox3/watch?bookId={BOOK_ID}&episode={ep_no}&lang=in'
    r = requests.get(url, headers=VIDRAMA_HDR, timeout=30, verify=False)
    if r.ok:
        data = r.json()
        if data.get('success'):
            urls = {}
            for q in data.get('availableQualities', []):
                if q['label'] in ['720p', '540p']:
                    urls[q['label']] = q['url']
            subtitles = data.get('subtitles', [])
            return urls, subtitles
    return {}, []

def upload_stream_to_r2(r2, stream_url, r2_key, quality_label):
    """Stream download video directly to R2 without saving to disk"""
    print(f"    ⬇ Streaming {quality_label} → R2...", end='', flush=True)
    r = requests.get(stream_url, headers=VIDRAMA_HDR, stream=True, timeout=120, verify=False)
    if not r.ok:
        print(f" ✗ HTTP {r.status_code}")
        return None
    
    content_type = 'video/mp4'
    size = 0
    buf = io.BytesIO()
    for chunk in r.iter_content(chunk_size=1024*1024):  # 1MB chunks
        if chunk:
            buf.write(chunk)
            size += len(chunk)
    
    buf.seek(0)
    r2.upload_fileobj(buf, R2_BUCKET, r2_key,
                      ExtraArgs={'ContentType': content_type, 'CacheControl': 'public, max-age=31536000'})
    print(f" ✓ {size/1024/1024:.1f}MB → {r2_key}")
    return f"{R2_PUBLIC}/{r2_key}"

def register_episode(drama_id, ep_no, video_url_720, video_url_540):
    """Register episode in admin panel, returns episode ID if successful"""
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': video_url_720 or video_url_540 or '',
        'videoUrl540p': video_url_540 or '',
        'isVip': False,
        'coinPrice': 0,
        'isActive': True,
    }
    r = requests.post(
        f"{API_BASE}/admin/dramas/{drama_id}/episodes",
        headers=ADMIN_HDR, json=payload, timeout=20
    )
    if r.ok:
        resp = r.json()
        return resp.get('id')
    else:
        print(f"    ✗ DB registration failed: {r.status_code} - {r.text[:200]}")
    return None

def register_subtitles(episode_id, subtitles_list):
    """Register subtitles for the episode"""
    count = 0
    for sub in subtitles_list:
        lang = sub.get('language') or sub.get('lang', '')
        label = sub.get('label') or sub.get('languageDisplayName', lang)
        url = sub.get('url') or sub.get('src', '')
        is_default = sub.get('default', False)
        if not url or not lang:
            continue
        payload = {'language': lang, 'label': label, 'url': url, 'isDefault': is_default}
        r = requests.post(
            f"{API_BASE}/episodes/{episode_id}/subtitles",
            headers=ADMIN_HDR, json=payload, timeout=15
        )
        if r.ok:
            count += 1
    return count

def main():
    print("=" * 60)
    print(f"JANJI KUNO BACKFILL PROCESS")
    print(f"Book ID: {BOOK_ID} | Drama ID: {DRAMA_ID}")
    print(f"Episodes to scrape: {START_EP} to {END_EP}")
    print("=" * 60)
    
    r2 = get_r2()
    success_count = 0
    fail_count = 0
    
    for ep_no in range(START_EP, END_EP + 1):
        print(f"\n📹 Episode {ep_no}/{END_EP}:")
        
        # 1. Fetch stream URLs from Vidrama
        stream_urls = {}
        subtitles_list = []
        for attempt in range(3):
            try:
                stream_urls, subtitles_list = get_episode_data(ep_no)
                if stream_urls:
                    break
            except Exception as e:
                print(f"    ⚠ Attempt {attempt+1} failed: {e}")
                time.sleep(3)
        
        if not stream_urls:
            print(f"    ✗ No stream URLs for EP {ep_no} after retries, skipping")
            fail_count += 1
            continue
            
        # 2. Upload to R2
        video_720_r2 = None
        video_540_r2 = None
        
        # Upload 720p
        if '720p' in stream_urls:
            key = f"dramas/{BOOK_SLUG}/ep{ep_no:03d}_720p.mp4"
            for attempt in range(3):
                try:
                    video_720_r2 = upload_stream_to_r2(r2, stream_urls['720p'], key, '720p')
                    if video_720_r2:
                        break
                except Exception as e:
                    print(f"    ⚠ 720p upload attempt {attempt+1} failed: {e}")
                    time.sleep(3)
                    
        # Upload 540p
        if '540p' in stream_urls:
            key = f"dramas/{BOOK_SLUG}/ep{ep_no:03d}_540p.mp4"
            for attempt in range(3):
                try:
                    video_540_r2 = upload_stream_to_r2(r2, stream_urls['540p'], key, '540p')
                    if video_540_r2:
                        break
                except Exception as e:
                    print(f"    ⚠ 540p upload attempt {attempt+1} failed: {e}")
                    time.sleep(3)
                    
        primary_url = video_720_r2 or video_540_r2
        if not primary_url:
            print(f"    ✗ EP {ep_no} - all video uploads failed, skipping registration")
            fail_count += 1
            continue
            
        # 3. Register in Database
        episode_id = register_episode(DRAMA_ID, ep_no, video_720_r2, video_540_r2)
        if episode_id:
            sub_count = register_subtitles(episode_id, subtitles_list)
            print(f"    ✓ EP {ep_no} registered | {sub_count} subtitle(s) registered")
            success_count += 1
        else:
            print(f"    ✗ EP {ep_no} failed to register in database")
            fail_count += 1
            
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"PROCESS COMPLETED!")
    print(f"Success: {success_count} / {END_EP - START_EP + 1}")
    print(f"Failed: {fail_count}")
    print("=" * 60)

if __name__ == '__main__':
    main()
