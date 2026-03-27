"""Test VIP auth access - check if VIP episodes now have HLS URLs"""
import sys, requests, re, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VIP_AUTH_PARAMS = (
    '%7B%22auth_key%22%3A%220mbsk7VVLt3JLNTqtC1EnJoK0pQAA3pW%22%2C'
    '%22auth_secret%22%3A%22DjRzZ0PoETLc8K9nq1N89pX2dtvuspc3%22%2C'
    '%22name%22%3A%22Seiman%20Zega%22%2C'
    '%22user_id%22%3A36848605951%2C'
    '%22user_type%22%3A1%7D'
)

H5_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8',
    'Referer': 'https://m.mydramawave.com/',
    'Cookie': f'auth_params={VIP_AUTH_PARAMS}',
}

# Test with drama that has VIP episodes - "Lulus Masa Percobaan, Hamil oleh Bosku(Sulih Suara)"
test_url = 'https://m.mydramawave.com/series/eNFDnztZRb/KhuqW30i3V'
print(f"Testing: {test_url}")

r = requests.get(test_url, headers=H5_HEADERS, timeout=25)
html = r.text

m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
if not m:
    print("ERROR: No __NUXT_DATA__ found!")
    sys.exit(1)

data = json.loads(m.group(1))
flat = data if isinstance(data, list) else []

# Find all m3u8 URLs
m3u8_urls = [v for v in flat if isinstance(v, str) and '.m3u8' in v]
print(f"\nFound {len(m3u8_urls)} m3u8 URLs:")
for u in m3u8_urls[:10]:
    print(f"  {u}")

# Check user_type in the data  
user_types = [v for v in flat if v == 1 or v == 2 or v == 3]
print(f"\nuser_type values found: {set(user_types)}")

# Count episodes with/without HLS vs nulls
nulls = flat.count(None)
total = len(flat)
print(f"\nTotal flat items: {total}, nulls: {nulls}, m3u8: {len(m3u8_urls)}")
