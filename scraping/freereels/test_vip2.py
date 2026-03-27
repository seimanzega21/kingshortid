"""Test VIP auth - series page"""
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

# Test with SERIES page (no episode key)
test_url = 'https://m.mydramawave.com/series/eNFDnztZRb'
print(f'Testing series page: {test_url}')
r = requests.get(test_url, headers=H5_HEADERS, timeout=25)
print(f'Final URL: {r.url}')
html = r.text

m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
if not m:
    print('No __NUXT_DATA__!')
    sys.exit()

data = json.loads(m.group(1))
flat = data if isinstance(data, list) else []
m3u8 = [v for v in flat if isinstance(v, str) and '.m3u8' in v]
print(f'Total flat: {len(flat)}, m3u8: {len(m3u8)}')
for u in m3u8[:5]:
    print(f'  {u[:120]}')

# Also check for "is_vip" or "free" field values
vip_flags = [v for v in flat if v in ['is_vip', 'is_free', 'vip', 'free', True, False]]
print(f'VIP/free flags: {set(str(v) for v in vip_flags[:20])}')
