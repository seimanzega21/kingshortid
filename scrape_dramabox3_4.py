# -*- coding: utf-8 -*-
"""
Scraper Dramabox3 - Full Pipeline
Drama: Menjebak di Dalam Jebakan (42000009069)
70 Episodes | Download 720p + 540p | Upload R2 | Register Admin
"""
import requests, boto3, sys, json, time, os, re, io
from botocore.config import Config
import urllib3

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

# ─── CONFIG ─────────────────────────────────────────────────────────────────
BOOK_ID     = '42000012098'
BOOK_SLUG   = 'ternyata-suamiku-penguasa-dunia'
TOTAL_EPS   = 90
START_EP    = 1
DRAMA_ID_EXISTING = 'd4y4iq97ijot9athzlex2zn9'

API_BASE    = 'https://api.shortlovers.id'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

COOKIE = '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCnv5004644=48; cf_clearance=N5A.kyHMnJ7RBK3hOyqybB6KddOTpRsZyEiE.fgp5kM-1779713242-1.2.1.1-9YHMfsNOniF6J54T1_JEaJY6mYbVJWOz8Kkm0raJacrpotGOYzyN_gG.Kxb7kfPxOO1wYdSenqFW0HIUwqQ57F5gqyjRbwvS8_r8rLFxIbYHNWMAahrr.iKy0dsa1krg8mVhzXDilHK71X.Iszvd8uo_CwVzbHiVUurJ8eF1DyguF2fK1vFa68H3Z5HFzZhBvVaIle1tEW3443.tH9TYjQX.7HKB9SBI2ZHkNto2vDQ2F77XP3cLmCp7GPXINCG8mrZf6l5xsxuh_xyqNp1bIRyxkUhz9IooxQKp3yV9Crri9TFW9II5q0M50yOlhCROGsKwa0AkIkKtWi.pNc5ATg; HstCla5004644=1779713242621; HstPn5004644=2; HstPt5004644=93; HstCns5004644=54; panoramaId_expiry=1779799644224'

VIDRAMA_HDR = {
  'accept': '*/*',
  'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
  'cookie': COOKIE,
  'priority': 'u=1, i',
  'referer': f'https://vidrama.asia/watch/menjebak-di-dalam-jebakan--{BOOK_ID}/1?provider=dramabox3&lang=in',
  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36'
}

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

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

def upload_cover_to_r2(r2, cover_url):
    """Download and upload cover image to R2"""
    r = requests.get(cover_url, timeout=30, verify=False)
    if not r.ok:
        return cover_url  # fallback to original
    key = f"dramas/{BOOK_SLUG}/cover.jpg"
    r2.upload_fileobj(io.BytesIO(r.content), R2_BUCKET, key,
                      ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'})
    url = f"{R2_PUBLIC}/{key}"
    print(f"  ✓ Cover uploaded: {url}")
    return url

def get_drama_metadata():
    """Get drama detail from vidrama API"""
    r = requests.get(
        f'https://vidrama.asia/api/dramabox3/drama/{BOOK_ID}?lang=in',
        headers=VIDRAMA_HDR, timeout=30, verify=False
    )
    if r.ok:
        d = r.json().get('data', {})
        return d
    return {}

def get_episode_data(ep_no):
    """Get stream URLs + subtitles for an episode"""
    r = requests.get(
        f'https://vidrama.asia/api/dramabox3/watch?bookId={BOOK_ID}&episode={ep_no}&lang=in',
        headers=VIDRAMA_HDR, timeout=30, verify=False
    )
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

def get_episode_stream_urls(ep_no):
    """Get 720p and 540p stream URLs for an episode"""
    urls, _ = get_episode_data(ep_no)
    return urls

def register_drama_in_admin(metadata, cover_r2_url):
    """Create drama entry in KingShort admin panel with status pending"""
    tags = metadata.get('tags', [])
    # Map to our known genres
    genre_map = {
        'Balas Dendam': 'Drama',
        'Serangan Balik': 'Drama',
        'Perselingkuhan': 'Romantis',
        'Penyesalan': 'Romantis',
        'Pura-pura Bodoh': 'Drama',
        'Modern': 'Drama',
        'Romance': 'Romantis',
        'Action': 'Action',
        'Comedy': 'Komedi',
        'Thriller': 'Thriller',
    }
    
    genres = list(set([genre_map.get(t, 'Drama') for t in tags]))[:3]
    if not genres:
        genres = ['Drama']
    
    book_status = metadata.get('bookStatus', 1)
    status = 'completed' if book_status == 2 else 'ongoing'  # bookStatus 1=ongoing, 2=completed
    
    payload = {
        'title': metadata.get('bookName', 'Menjebak di Dalam Jebakan'),
        'description': metadata.get('introduction', ''),
        'cover': cover_r2_url,
        'genres': genres,
        'totalEpisodes': metadata.get('chapterCount', TOTAL_EPS),
        'status': status,
        'country': 'Indonesia',
        'language': 'Indonesia',
        'isActive': False,  # pending = not active yet
        'isVip': False,
    }
    
    print(f"\n📋 Registering drama in admin panel...")
    print(f"   Title: {payload['title']}")
    print(f"   Genres: {payload['genres']}")
    print(f"   Total Episodes: {payload['totalEpisodes']}")
    print(f"   Status: {payload['status']}")
    
    r = requests.post(f"{API_BASE}/api/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        resp = r.json()
        drama_id = resp.get('id') or resp.get('drama', {}).get('id')
        print(f"   ✓ Drama registered! ID: {drama_id}")
        return drama_id
    else:
        print(f"   ✗ Failed: {r.status_code} {r.text[:200]}")
        return None

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
        f"{API_BASE}/api/admin/dramas/{drama_id}/episodes",
        headers=ADMIN_HDR, json=payload, timeout=20
    )
    if r.ok:
        resp = r.json()
        return resp.get('id')
    return None

def register_subtitles(episode_id, subtitles_list):
    """Register all subtitles for an episode"""
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
            f"{API_BASE}/api/episodes/{episode_id}/subtitles",
            headers=ADMIN_HDR, json=payload, timeout=15
        )
        if r.ok:
            count += 1
    return count

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("SCRAPER RESUME: Ternyata Suamiku Penguasa Dunia")
    print(f"Book ID: {BOOK_ID} | Resuming from EP {START_EP}")
    print("=" * 60)
    
    r2 = get_r2()
    drama_id = DRAMA_ID_EXISTING
    print(f"\n✓ Using existing drama ID: {drama_id}")
    print(f"✓ Starting from episode {START_EP}/{TOTAL_EPS}\n")
    
    success_count = 0
    fail_count = 0
    
    for ep_no in range(START_EP, TOTAL_EPS + 1):
        print(f"\n  📹 Episode {ep_no}/{TOTAL_EPS}:")
        
        # Get stream URLs + subtitles - retry up to 3 times
        stream_urls = {}
        subtitle_list = []
        for attempt in range(3):
            try:
                stream_urls, subtitle_list = get_episode_data(ep_no)
                if stream_urls:
                    break
            except Exception as e:
                print(f"    ⚠ Attempt {attempt+1} failed: {e}")
                time.sleep(3)
        
        if not stream_urls:
            print(f"    ✗ No stream URLs for EP {ep_no} after retries, skipping")
            fail_count += 1
            continue
        
        video_720_r2 = None
        video_540_r2 = None
        
        # Upload 720p with retry
        if '720p' in stream_urls:
            key = f"dramas/{BOOK_SLUG}/ep{ep_no:03d}_720p.mp4"
            for attempt in range(3):
                try:
                    video_720_r2 = upload_stream_to_r2(r2, stream_urls['720p'], key, '720p')
                    if video_720_r2:
                        break
                except Exception as e:
                    print(f"    ⚠ 720p attempt {attempt+1} failed: {e}")
                    time.sleep(3)
        
        # Upload 540p with retry
        if '540p' in stream_urls:
            key = f"dramas/{BOOK_SLUG}/ep{ep_no:03d}_540p.mp4"
            for attempt in range(3):
                try:
                    video_540_r2 = upload_stream_to_r2(r2, stream_urls['540p'], key, '540p')
                    if video_540_r2:
                        break
                except Exception as e:
                    print(f"    ⚠ 540p attempt {attempt+1} failed: {e}")
                    time.sleep(3)
        
        # If 720p failed entirely, still try to use 540p as primary
        primary_url = video_720_r2 or video_540_r2
        if not primary_url:
            print(f"    ✗ EP {ep_no} - all uploads failed, skipping registration")
            fail_count += 1
            continue
        
        # Register episode in admin
        episode_id = register_episode(drama_id, ep_no, video_720_r2, video_540_r2)
        if episode_id:
            # Register subtitles immediately
            sub_count = register_subtitles(episode_id, subtitle_list)
            print(f"    ✓ EP {ep_no} registered | {sub_count} subtitle(s)")
            success_count += 1
        else:
            print(f"    ✗ EP {ep_no} failed to register in admin")
            fail_count += 1
        
        # Small delay
        time.sleep(0.3)
    
    print("\n" + "=" * 60)
    print(f"✅ DONE! Success: {success_count}, Failed: {fail_count}")
    print(f"Drama ID in KingShort: {drama_id}")
    print(f"Status: PENDING (isActive=False) - Review in admin panel")
    print("=" * 60)

if __name__ == '__main__':
    main()

