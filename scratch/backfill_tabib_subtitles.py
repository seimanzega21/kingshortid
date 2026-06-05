# -*- coding: utf-8 -*-
import requests
import boto3
import sys
import json
import time
import os
import argparse
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

DRAMA_DB_ID = 'dm4pug3ppvsaqrbppinxvu9w'
NS_ID = '2049782344826486786'
SLUG = 'tabib-pelindung-negeri'

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def refresh_cookies_via_playwright():
    global WEB_HDRS, COOKIE
    print("   [PLAYWRIGHT] Cookie expired or Cloudflare challenged. Refreshing cookies via Playwright...")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir='d:/kingshortid/scripts/melolo-scraper/vidrama_profile',
                headless=True
            )
            page = context.new_page()
            page.goto('https://vidrama.asia/')
            page.wait_for_timeout(2500)
            cookies = context.cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            COOKIE = cookie_str
            WEB_HDRS['Cookie'] = cookie_str
            print("   [PLAYWRIGHT] Cookies refreshed successfully!")
            context.close()
            return True
    except Exception as e:
        print(f"   [PLAYWRIGHT] Error refreshing cookies: {e}")
        return False

def get_db_episodes(db_id):
    url = f"{API_BASE}/dramas/{db_id}/episodes?includeInactive=true"
    r = requests.get(url, headers=ADMIN_HDR, timeout=15)
    if r.ok:
        eps = r.json()
        ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
        return {e.get('episodeNumber'): e.get('id') for e in ep_list if e.get('episodeNumber')}
    return {}

def get_episode_data(ns_id, ep_no):
    url = f"https://vidrama.asia/api/netshortv2/episode/{ns_id}/{ep_no}?lang=in"
    for attempt in range(3):
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=20, verify=False)
            if r.ok:
                data = r.json()
                if data.get('code') == 200:
                    return data.get('data', {})
                else:
                    print(f"      ⚠ API returned code {data.get('code')}: {data.get('msg')}")
            else:
                print(f"      ⚠ HTTP error {r.status_code}")
                
            if not r.ok or r.status_code == 403 or (r.ok and r.json().get('code') != 200):
                refresh_cookies_via_playwright()
        except Exception as e:
            print(f"      ⚠ Request exception: {e}")
            refresh_cookies_via_playwright()
            
    # Playwright Fallback
    try:
        print("      [PLAYWRIGHT] Fallback: Fetching episode data directly using Playwright...")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir='d:/kingshortid/scripts/melolo-scraper/vidrama_profile',
                headless=True
            )
            page = context.new_page()
            page.goto(url)
            page.wait_for_timeout(2000)
            content = page.inner_text("body")
            context.close()
            data = json.loads(content)
            if data.get('code') == 200:
                return data.get('data', {})
    except Exception as e:
        print(f"      [PLAYWRIGHT] Error in fallback episode fetch: {e}")
        
    return {}

def main():
    parser = argparse.ArgumentParser(description="Backfill Tabib Pelindung Negeri subtitles")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying anything")
    args = parser.parse_args()

    print("=" * 60)
    print("TABIB PELINDUNG NEGERI SUBTITLE BACKFILL PIPELINE")
    print("=" * 60)
    if args.dry_run:
        print("!!! DRY RUN MODE ACTIVE !!!")
        print("=" * 60)

    # 1. Fetch DB episodes mapping
    print("Fetching episodes from database...")
    db_eps = get_db_episodes(DRAMA_DB_ID)
    print(f"Total episodes in DB: {len(db_eps)}")

    if not db_eps:
        print("✗ No episodes found in database. Exiting.")
        return

    r2 = None if args.dry_run else get_r2()
    success_count = 0

    # Sort episodes to process sequentially
    sorted_eps = sorted(db_eps.keys())

    for idx, ep_no in enumerate(sorted_eps, start=1):
        ep_id = db_eps[ep_no]
        print(f"\n🎬 [{idx}/{len(sorted_eps)}] Processing Episode {ep_no}:")

        if args.dry_run:
            print(f"     [DRY RUN] Would fetch subtitles for EP {ep_no} and register to DB ID {ep_id}")
            continue

        # Fetch episode details from upstream
        ep_data = {}
        for attempt in range(5):
            ep_data = get_episode_data(NS_ID, ep_no)
            if ep_data and ep_data.get('subtitles'):
                break
            print(f"     Waiting 8 seconds before retry {attempt+2}/5...")
            time.sleep(8)

        if not ep_data:
            print("     ✗ Failed to fetch episode data")
            continue

        subtitles = ep_data.get('subtitles', [])
        if not subtitles:
            print("     ✗ No subtitles found upstream")
            continue

        # Find Indonesia subtitle (id_ID)
        indonesia_sub = next((s for s in subtitles if s.get('language') == 'id_ID'), None)
        if not indonesia_sub and subtitles:
            indonesia_sub = subtitles[0] # Fallback

        if not indonesia_sub:
            print("     ✗ No Indonesian subtitle found")
            continue

        sub_url = indonesia_sub.get('url') or indonesia_sub.get('src')
        if not sub_url:
            print("     ✗ Subtitle URL is empty")
            continue

        sub_key = f"netshortv2/{SLUG}/ep{ep_no:03d}.vtt"
        try:
            print("     ⬇ Downloading subtitle VTT...", end="", flush=True)
            sub_r = requests.get(sub_url, headers=WEB_HDRS, timeout=15, verify=False)
            if sub_r.ok:
                print(" ✓ Success")
                # Upload to R2
                print("     ⬆ Uploading to R2...", end="", flush=True)
                r2.put_object(Bucket=R2_BUCKET, Key=sub_key, Body=sub_r.content, ContentType='text/vtt')
                final_sub_url = f"{R2_PUBLIC}/{sub_key}"
                print(" ✓ Done")

                # Register in database
                payload = {
                    'language': 'indonesia',
                    'label': 'Indonesia',
                    'url': final_sub_url,
                    'isDefault': True
                }
                print("     ⚙ Registering in DB...", end="", flush=True)
                db_r = requests.post(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=payload, timeout=15)
                if db_r.ok:
                    print(" ✓ Success")
                    success_count += 1
                else:
                    print(f" ✗ DB failed: {db_r.status_code} - {db_r.text}")
            else:
                print(f" ✗ Download failed HTTP {sub_r.status_code}")
        except Exception as e:
            print(f"     ✗ Error: {e}")

        time.sleep(2.0)

    print("\n" + "=" * 60)
    print(f"SUBTITLE BACKFILL COMPLETED: {success_count}/{len(sorted_eps)} subtitles updated successfully")
    print("=" * 60)

if __name__ == '__main__':
    main()
