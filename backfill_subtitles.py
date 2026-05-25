# -*- coding: utf-8 -*-
"""
Subtitle Backfill Script
- Fetch all episodes from KingShort API for drama byv3jp8t6vuqbnyxhfk08qlk
- For each episode, get subtitle URLs from vidrama watch API
- Register Indonesian subtitle to each episode
"""
import requests, json, sys, time, urllib3
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

# ── CONFIG
DRAMA_ID    = 'byv3jp8t6vuqbnyxhfk08qlk'
BOOK_ID     = '42000009069'
API_BASE    = 'https://api.shortlovers.id'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

COOKIE = '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCnv5004644=48; cf_clearance=N5A.kyHMnJ7RBK3hOyqybB6KddOTpRsZyEiE.fgp5kM-1779713242-1.2.1.1-9YHMfsNOniF6J54T1_JEaJY6mYbVJWOz8Kkm0raJacrpotGOYzyN_gG.Kxb7kfPxOO1wYdSenqFW0HIUwqQ57F5gqyjRbwvS8_r8rLFxIbYHNWMAahrr.iKy0dsa1krg8mVhzXDilHK71X.Iszvd8uo_CwVzbHiVUurJ8eF1DyguF2fK1vFa68H3Z5HFzZhBvVaIle1tEW3443.tH9TYjQX.7HKB9SBI2ZHkNto2vDQ2F77XP3cLmCp7GPXINCG8mrZf6l5xsxuh_xyqNp1bIRyxkUhz9IooxQKp3yV9Crri9TFW9II5q0M50yOlhCROGsKwa0AkIkKtWi.pNc5ATg; HstCla5004644=1779713242621; HstPn5004644=2; HstPt5004644=93; HstCns5004644=54; panoramaId_expiry=1779799644224'

VIDRAMA_HDR = {
    'accept': '*/*',
    'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'cookie': COOKIE,
    'priority': 'u=1, i',
    'referer': f'https://vidrama.asia/watch/menjebak-di-dalam-jebakan--{BOOK_ID}/1?provider=dramabox3&lang=in',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36'
}

def get_all_episodes():
    """Get all episodes from KingShort admin API"""
    # Try public endpoint first (works for pending dramas via includeInactive)
    r = requests.get(f'{API_BASE}/api/dramas/{DRAMA_ID}/episodes', headers=ADMIN_HDR, timeout=30)
    if r.ok:
        data = r.json()
        if isinstance(data, list):
            return data
        return data.get('episodes', data.get('data', []))
    
    # Try admin episodes endpoint
    r2 = requests.get(f'{API_BASE}/api/episodes?dramaId={DRAMA_ID}', headers=ADMIN_HDR, timeout=30)
    if r2.ok:
        data = r2.json()
        if isinstance(data, list):
            return data
        return data.get('episodes', data.get('data', []))
    
    print(f"Failed to get episodes: {r.status_code} {r.text[:200]}")
    return []


def get_subtitle_urls_from_vidrama(ep_no):
    """Get subtitle URLs from vidrama watch API"""
    url = f'https://vidrama.asia/api/dramabox3/watch?bookId={BOOK_ID}&episode={ep_no}&lang=in'
    try:
        r = requests.get(url, headers=VIDRAMA_HDR, timeout=30, verify=False)
        if r.ok:
            data = r.json()
            if data.get('success'):
                return data.get('subtitles', [])
    except Exception as e:
        print(f"    Error fetching subtitles for EP {ep_no}: {e}")
    return []

def register_subtitle(episode_id, language, label, url, is_default):
    """Register a subtitle for an episode"""
    payload = {
        'language': language,
        'label': label,
        'url': url,
        'isDefault': is_default
    }
    r = requests.post(
        f'{API_BASE}/api/episodes/{episode_id}/subtitles',
        headers=ADMIN_HDR, json=payload, timeout=15
    )
    return r.ok

def main():
    print("=" * 60)
    print("SUBTITLE BACKFILL: Menjebak di Dalam Jebakan")
    print(f"Drama ID: {DRAMA_ID}")
    print("=" * 60)

    # Get all episodes currently in DB
    print("\n[1/2] Fetching episodes from admin panel...")
    episodes = get_all_episodes()
    print(f"  Found {len(episodes)} episodes")
    
    if not episodes:
        print("No episodes found! Drama may not have episodes yet.")
        print("Will try by episode number directly (1-70)...")
        # Fallback: use episode numbers 1-70 manually
        episodes = [{'id': None, 'episodeNumber': i} for i in range(1, 71)]

    # Sort by episode number
    episodes.sort(key=lambda x: x.get('episodeNumber', x.get('episode_number', 0)))

    print(f"\n[2/2] Fetching & registering subtitles for {len(episodes)} episodes...")
    
    success = 0
    fail = 0

    for ep in episodes:
        ep_id = ep.get('id')
        ep_no = ep.get('episodeNumber') or ep.get('episode_number', 0)
        
        if not ep_id:
            print(f"  EP {ep_no}: No episode ID, skipping")
            continue

        print(f"  EP {ep_no} (id={ep_id[:8]}...):", end='', flush=True)
        
        # Get subtitle URLs from vidrama
        subtitle_list = get_subtitle_urls_from_vidrama(ep_no)
        
        if not subtitle_list:
            print(f" ✗ No subtitles from API")
            fail += 1
            continue
        
        # Register each subtitle language (prioritize Indonesian)
        ep_registered = 0
        for sub in subtitle_list:
            lang = sub.get('language') or sub.get('lang', '')
            label = sub.get('label') or sub.get('languageDisplayName', lang)
            url = sub.get('url') or sub.get('src', '')
            is_default = sub.get('default', False)
            
            if not url or not lang:
                continue
            
            ok = register_subtitle(ep_id, lang, label, url, is_default)
            if ok:
                ep_registered += 1
        
        if ep_registered > 0:
            print(f" ✓ {ep_registered} subtitle(s) registered")
            success += 1
        else:
            print(f" ✗ Failed to register any subtitle")
            fail += 1
        
        time.sleep(0.3)  # Be polite

    print("\n" + "=" * 60)
    print(f"✅ DONE! Success: {success}, Failed: {fail}")
    print("=" * 60)

if __name__ == '__main__':
    main()
