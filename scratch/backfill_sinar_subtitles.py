# -*- coding: utf-8 -*-
import requests
import boto3
import json
import urllib3
import sys
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

DRAMA_DB_ID = 'o8wdjeeh9y5iq7puuq8c689h'
NS_ID = '2056946805631225858'
SLUG = 'mencari-sinar-di-lautan'

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def main():
    print("=" * 60)
    print("MENCARI SINAR DI LAUTAN SUBTITLE BACKFILL")
    print("=" * 60)

    # 1. Fetch episodes from DB
    print("Fetching episodes from DB...")
    r = requests.get(f"{API_BASE}/dramas/{DRAMA_DB_ID}/episodes?includeInactive=true", headers=ADMIN_HDR)
    if not r.ok:
        print("Failed to get episodes from DB")
        return
    
    eps = r.json()
    ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
    print(f"Loaded {len(ep_list)} episodes from DB")

    r2 = get_r2()
    success_count = 0

    # Sort episodes by episodeNumber
    for ep in sorted(ep_list, key=lambda x: x.get('episodeNumber', 0)):
        ep_no = ep.get('episodeNumber')
        ep_id = ep.get('id')

        print(f"\n📹 Episode {ep_no}:")

        # Query upstream for subtitles
        url = f"https://vidrama.asia/api/netshortv2/episode/{NS_ID}/{ep_no}?lang=in"
        subtitles = []
        try:
            res = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
            if res.ok:
                data = res.json()
                if data.get('code') == 200:
                    subtitles = data.get('data', {}).get('subtitles', [])
                else:
                    print(f"   ⚠ API returned code {data.get('code')}: {data.get('message')}")
            else:
                print(f"   ⚠ HTTP error {res.status_code}")
        except Exception as e:
            print(f"   ⚠ Request exception: {e}")
            continue

        if not subtitles:
            print("   ✗ No subtitles found upstream")
            continue

        # Choose id_ID language
        indonesia_sub = next((s for s in subtitles if s.get('language') == 'id_ID'), None)
        if not indonesia_sub and subtitles:
            indonesia_sub = subtitles[0] # fallback

        if not indonesia_sub:
            print("   ✗ No Indonesian subtitle found")
            continue

        sub_url = indonesia_sub.get('url') or indonesia_sub.get('src')
        if not sub_url:
            print("   ✗ Subtitle URL is empty")
            continue

        # Download subtitle from upstream
        sub_key = f"netshortv2/{SLUG}/ep{ep_no:03d}.vtt"
        try:
            print("   ⬇ Downloading VTT...", end="", flush=True)
            sub_r = requests.get(sub_url, headers=WEB_HDRS, timeout=15, verify=False)
            if sub_r.ok:
                print(" ✓ Success")
                # Upload to R2
                print("   ⬆ Uploading to R2...", end="", flush=True)
                r2.put_object(Bucket=R2_BUCKET, Key=sub_key, Body=sub_r.content, ContentType='text/vtt')
                final_sub_url = f"{R2_PUBLIC}/{sub_key}"
                print(" ✓ Uploaded")

                # Register in database using "indonesia" language code
                payload = {
                    'language': 'indonesia',
                    'label': 'Indonesia',
                    'url': final_sub_url,
                    'isDefault': True
                }
                print("   ⚙ Registering in DB...", end="", flush=True)
                db_r = requests.post(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=payload, timeout=15)
                if db_r.ok:
                    print(" ✓ Registered successfully")
                    success_count += 1
                else:
                    print(f" ✗ DB failed: {db_r.status_code} - {db_r.text}")
            else:
                print(f" ✗ Download failed HTTP {sub_r.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

    print("\n" + "=" * 60)
    print(f"SUBTITLE BACKFILL COMPLETED: {success_count}/{len(ep_list)} subtitles updated successfully")
    print("=" * 60)

if __name__ == '__main__':
    main()
