"""Test VIP auth - FIXED cookie encoding (curly braces NOT encoded)"""
import sys, requests, re, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# CORRECT encoding: { and } NOT encoded, only inner " encoded as %22
VIP_AUTH_PARAMS = '{%22auth_key%22:%220mbsk7VVLt3JLNTqtC1EnJoK0pQAA3pW%22,%22auth_secret%22:%22DjRzZ0PoETLc8K9nq1N89pX2dtvuspc3%22,%22name%22:%22Seiman%20Zega%22,%22user_id%22:36848605951,%22user_type%22:1}'

H5_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8',
    'Referer': 'https://m.mydramawave.com/',
    'Cookie': f'auth_params={VIP_AUTH_PARAMS}',
}

# UUID pattern
UUID_PAT = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

# Test series page - "Bos Kuliah Lagi" - find video UUIDs
SERIES_KEY = 'eNFDnztZRb'  # Lulus Masa Percobaan
print(f'Testing series: {SERIES_KEY}')
r = requests.get(f'https://m.mydramawave.com/series/{SERIES_KEY}', headers=H5_HEADERS, timeout=25)

m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
if not m:
    print('No __NUXT_DATA__!')
    sys.exit()

data = json.loads(m.group(1))
flat = data if isinstance(data, list) else []

# Find all UUIDs in flat array
uuids = [v for v in flat if isinstance(v, str) and UUID_PAT.fullmatch(v)]
m3u8 = [v for v in flat if isinstance(v, str) and '.m3u8' in v]
video_urls = [v for v in flat if isinstance(v, str) and 'video-v' in v]

print(f'Flat items: {len(flat)}, UUIDs: {len(uuids)}, m3u8: {len(m3u8)}, video CDN: {len(video_urls)}')
print(f'\nUUIDs found:')
for u in uuids[:10]:
    print(f'  {u}')
print(f'\nm3u8 URLs:')
for u in m3u8[:5]:
    print(f'  {u}')
print(f'\nVideo CDN URLs:')    
for u in video_urls[:5]:
    print(f'  {u}')

# Also check for videoUrl field
raw = json.dumps(flat)
video_mentions = re.findall(r'(videoUrl|hlsUrl|video_url|video_id)[^"]*"([^"]{10,})"', raw)
print(f'\nvideoUrl/hlsUrl mentions: {len(video_mentions)}')
for k, v in video_mentions[:5]:
    print(f'  {k}: {v[:80]}')
