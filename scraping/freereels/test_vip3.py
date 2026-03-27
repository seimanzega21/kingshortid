"""Test: get episode keys from series page, then fetch individual episode page for HLS URL"""
import sys, requests, re, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VIP_AUTH_PARAMS = (
    '%7B%22auth_key%22%3A%220mbsk7VVLt3JLNTqtC1EnJoK0pQAA3pW%22%2C'
    '%22auth_secret%22%3A%22DjRzZ0PoETLc8K9nq1N89pX2dtvuspc3%22%2C'
    '%22user_id%22%3A36848605951%2C%22user_type%22%3A1%7D'
)
H5_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8',
    'Referer': 'https://m.mydramawave.com/',
    'Cookie': f'auth_params={VIP_AUTH_PARAMS}',
}

# 1. Get series page and extract episode keys
series_url = 'https://m.mydramawave.com/series/eNFDnztZRb'
print(f'1. Fetching series: {series_url}')
r = requests.get(series_url, headers=H5_HEADERS, timeout=25)
html = r.text

# Look for episode key patterns in HTML (short alphanumeric keys)
ep_keys = re.findall(r'/series/eNFDnztZRb/([A-Za-z0-9_-]{8,12})', html)
ep_keys = list(dict.fromkeys(ep_keys))  # dedupe
print(f'Episode keys found: {len(ep_keys)}')
for k in ep_keys[:5]:
    print(f'  {k}')

# 2. Test individual episode page (first VIP episode)
if ep_keys:
    ep_key = ep_keys[0]  # Try first episode
    ep_url = f'https://m.mydramawave.com/series/eNFDnztZRb/{ep_key}'
    print(f'\n2. Fetching episode page: {ep_url}')
    r2 = requests.get(ep_url, headers=H5_HEADERS, timeout=25)
    html2 = r2.text
    
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html2, re.DOTALL)
    if m:
        data = json.loads(m.group(1))
        flat = data if isinstance(data, list) else []
        m3u8 = [v for v in flat if isinstance(v, str) and '.m3u8' in v]
        print(f'  flat items: {len(flat)}, m3u8 URLs: {len(m3u8)}')
        for u in m3u8[:3]:
            print(f'  HLS: {u[:100]}')
    else:
        print('  No __NUXT_DATA__ on episode page!')

# 3. Also test the known VIP episode from the user's browser
print('\n3. Testing known VIP episode from user (KhuqW30i3V):')
vip_url = 'https://m.mydramawave.com/series/eNFDnztZRb/KhuqW30i3V'
r3 = requests.get(vip_url, headers=H5_HEADERS, timeout=25)
html3 = r3.text
m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html3, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    flat = data if isinstance(data, list) else []
    m3u8 = [v for v in flat if isinstance(v, str) and '.m3u8' in v]
    print(f'  flat items: {len(flat)}, m3u8 URLs: {len(m3u8)}')
    for u in m3u8[:3]:
        print(f'  HLS: {u[:100]}')
