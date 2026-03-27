"""Test with FULL auth cookies - _session + auth_params"""
import sys, requests, re, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Full session cookie from browser (VIP Facebook session)
SESSION = 'eyJpdil6lmlI3MDh1WFdzcEZ3Z1FOd2g4a041cVE9PSIsInZhbHVlIjoiTUlCCUzZLcFNYSWVPRU1CNUdvQzhjMStKeE13N0NTZVhMRU8zRVIWQ2tHaUICQm1VcGswd0l5d054Y1ZydTZ6b0JqMTY4U3ZtWWEzUDhCVUYvTjJRa2dDV2hGSy93WnhzVUwxd0VlY1FUR3hBaFJ6bms0Q2NuaHRpTEpsbCs0Z2MiLCJtYWMiOiI2MzhiNWJjNzhjMjY0N2JiZDA4MTJiMTc0OGFhODc2MDM0MzlhOTA5ZjFlNzJkYmZiMWNlYzZmNjlIMWE1OTBkIiwidGFnIjoiln0%3D'

AUTH_PARAMS = '{%22auth_key%22:%220mbsk7VVLt3JLNTqtC1EnJoK0pQAA3pW%22,%22auth_secret%22:%22DjRzZ0PoETLc8K9nq1N89pX2dtvuspc3%22,%22name%22:%22Seiman%20Zega%22,%22user_id%22:36848605951,%22user_type%22:1}'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8',
    'Referer': 'https://m.mydramawave.com/',
    'Cookie': f'_session={SESSION}; auth_params={AUTH_PARAMS}',
}

UUID_PAT = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

# Test series + episode page 
tests = [
    ('Series only', 'https://m.mydramawave.com/series/eNFDnztZRb'),
    ('Episode page', 'https://m.mydramawave.com/series/eNFDnztZRb/KhuqW30i3V'),
]

for name, url in tests:
    print(f'\n=== {name}: {url} ===')
    r = requests.get(url, headers=HEADERS, timeout=25)
    print(f'Status: {r.status_code}, Final URL: {r.url}')
    
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
    if not m:
        print('NO __NUXT_DATA__!')
        continue
    
    data = json.loads(m.group(1))
    flat = data if isinstance(data, list) else []
    uuids = [v for v in flat if isinstance(v, str) and UUID_PAT.fullmatch(v)]
    m3u8s = [v for v in flat if isinstance(v, str) and '.m3u8' in v]
    video_cdn = [v for v in flat if isinstance(v, str) and 'video-v' in v]
    
    print(f'Flat: {len(flat)}, UUIDs: {len(uuids)}, m3u8: {len(m3u8s)}, CDN: {len(video_cdn)}')
    for u in uuids[:5]: print(f'  UUID: {u}')
    for u in m3u8s[:3]: print(f'  m3u8: {u[:100]}')
    for u in video_cdn[:3]: print(f'  CDN: {u[:100]}')
