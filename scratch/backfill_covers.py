# -*- coding: utf-8 -*-
import requests
import boto3
import json
import io
import sys
import re
import urllib3
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

# ─── CONFIG ─────────────────────────────────────────────────────────────────
API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET = 'shortlovers'
R2_PUBLIC = 'https://stream.shortlovers.id'

COOKIE = '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCnv5004644=48; cf_clearance=N5A.kyHMnJ7RBK3hOyqybB6KddOTpRsZyEiE.fgp5kM-1779713242-1.2.1.1-9YHMfsNOniF6J54T1_JEaJY6mYbVJWOz8Kkm0raJacrpotGOYzyN_gG.Kxb7kfPxOO1wYdSenqFW0HIUwqQ57F5gqyjRbwvS8_r8rLFxIbYHNWMAahrr.iKy0dsa1krg8mVhzXDilHK71X.Iszvd8uo_CwVzbHiVUurJ8eF1DyguF2fK1vFa68H3Z5HFzZhBvVaIle1tEW3443.tH9TYjQX.7HKB9SBI2ZHkNto2vDQ2F77XP3cLmCp7GPXINCG8mrZf6l5xsxuh_xyqNp1bIRyxkUhz9IooxQKp3yV9Crri9TFW9II5q0M50yOlhCROGsKwa0AkIkKtWi.pNc5ATg; HstCla5004644=1779713242621; HstPn5004644=2; HstPt5004644=93; HstCns5004644=54; panoramaId_expiry=1779799644224'

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': COOKIE
}

WORKSPACE_DIR = Path(__file__).resolve().parent.parent

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def make_slug(title):
    s = title.strip().lower()
    s = s.replace("(dubbing)", "")
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '-', s)
    return s.strip('-')

def main():
    print("=" * 60)
    print("NETSHORTV2 COVER BACKFILL PIPELINE")
    print("=" * 60)

    # 1. Load mapping
    try:
        with open(WORKSPACE_DIR / 'scratch' / 'mapped_netshortv2_dramas.json', 'r') as f:
            mapped = json.load(f)
    except Exception as e:
        print(f"Failed to load mapped dramas: {e}")
        return

    r2 = get_r2()
    success_count = 0

    # 2. Iterate through dramas
    for idx, item in enumerate(mapped, start=1):
        title = item['title']
        db_id = item['db_id']
        ns_id = item['netshort_id']
        slug = make_slug(title)

        print(f"\n🎬 [{idx}/{len(mapped)}] {title}")
        print(f"   DB ID: {db_id} | Netshort ID: {ns_id} | Slug: {slug}")

        # A. Fetch detail from Vidrama
        url = f"https://vidrama.asia/api/netshortv2/detail/{ns_id}?lang=id_ID"
        cover_url = None
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
            if r.ok:
                data = r.json()
                if data.get('code') == 200:
                    d = data.get('data', {})
                    cover_url = d.get('cover')
                else:
                    print(f"   ⚠ API returned code {data.get('code')}: {data.get('message')}")
            else:
                print(f"   ⚠ HTTP error {r.status_code}")
        except Exception as e:
            print(f"   ⚠ Failed to get detail: {e}")

        if not cover_url:
            print("   ✗ Cover URL not found in API response")
            continue

        # Try to clean the resize modifier to get original high resolution image
        # Example: webp resize parameter '~tplv-vod-rs:540:720.webp'
        clean_cover_url = cover_url.split('~tplv-')[0]
        print(f"   Original Cover URL: {clean_cover_url}")

        # B. Download cover
        try:
            print("   ⬇ Downloading cover...", end="", flush=True)
            cr = requests.get(clean_cover_url, timeout=20, verify=False)
            if not cr.ok:
                # fallback to raw cover URL
                print(" (retrying original resize URL)...", end="", flush=True)
                cr = requests.get(cover_url, timeout=20, verify=False)

            if cr.ok:
                print(" ✓ Success")
                # C. Upload to R2
                content_type = cr.headers.get('Content-Type', 'image/jpeg')
                # Determine extension
                ext = '.jpg'
                if 'image/webp' in content_type:
                    ext = '.webp'
                elif 'image/png' in content_type:
                    ext = '.png'
                
                key = f"dramas/{slug}/cover{ext}"
                print(f"   ⬆ Uploading to R2: {key}...", end="", flush=True)
                
                r2.upload_fileobj(
                    io.BytesIO(cr.content), R2_BUCKET, key,
                    ExtraArgs={'ContentType': content_type, 'CacheControl': 'public, max-age=31536000'}
                )
                r2_cover_url = f"{R2_PUBLIC}/{key}"
                print(" ✓ Uploaded")

                # D. Update database
                payload = {'cover': r2_cover_url}
                print(f"   ⚙ Patching DB...", end="", flush=True)
                db_url = f"{API_BASE}/admin/dramas/{db_id}"
                db_r = requests.patch(db_url, headers=ADMIN_HDR, json=payload, timeout=15)
                if db_r.ok:
                    print(" ✓ Patched successfully")
                    success_count += 1
                else:
                    print(f" ✗ DB update failed: {db_r.status_code} - {db_r.text}")
            else:
                print(" ✗ Download failed")
        except Exception as e:
            print(f"   ✗ Error processing cover: {e}")

    print("\n" + "=" * 60)
    print(f"COVER BACKFILL COMPLETED: {success_count}/{len(mapped)} updated successfully")
    print("=" * 60)

if __name__ == '__main__':
    main()
