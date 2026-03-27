"""Probe all strings in flat array + Nuxt API endpoints"""
import sys, requests, re, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SESSION = 'eyJpdil6lmlI3MDh1WFdzcEZ3Z1FOd2g4a041cVE9PSIsInZhbHVlIjoiTUlCCUzZLcFNYSWVPRU1CNUdvQzhjMStKeE13N0NTZVhMRU8zRVIWQ2tHaUICQm1VcGswd0l5d054Y1ZydTZ6b0JqMTY4U3ZtWWEzUDhCVUYvTjJRa2dDV2hGSy93WnhzVUwxd0VlY1FUR3hBaFJ6bms0Q2NuaHRpTEpsbCs0Z2MiLCJtYWMiOiI2MzhiNWJjNzhjMjY0N2JiZDA4MTJiMTc0OGFhODc2MDM0MzlhOTA5ZjFlNzJkYmZiMWNlYzZmNjlIMWE1OTBkIiwidGFnIjoiln0%3D'
AUTH_PARAMS = '{%22auth_key%22:%220mbsk7VVLt3JLNTqtC1EnJoK0pQAA3pW%22,%22auth_secret%22:%22DjRzZ0PoETLc8K9nq1N89pX2dtvuspc3%22,%22name%22:%22Seiman%20Zega%22,%22user_id%22:36848605951,%22user_type%22:1}'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8',
    'Referer': 'https://m.mydramawave.com/',
    'Cookie': f'_session={SESSION}; auth_params={AUTH_PARAMS}',
}
API_HEADERS = {**HEADERS, 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}

SERIES = 'eNFDnztZRb'
EP_KEY = 'KhuqW30i3V'

# 1. Show ALL strings in flat array of episode page
print('=== 1. ALL STRINGS IN FLAT ARRAY (episode page) ===')
r = requests.get(f'https://m.mydramawave.com/series/{SERIES}/{EP_KEY}', headers=HEADERS, timeout=25)
m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
if m:
    flat = json.loads(m.group(1))
    strings = [v for v in flat if isinstance(v, str) and len(v) > 5]
    print(f'Total strings (>5 chars): {len(strings)}')
    for s in strings:
        print(f'  {repr(s[:120])}')

print('\n=== 2. PROBE NUXT API ENDPOINTS ===')
api_paths = [
    f'/api/series/{SERIES}/{EP_KEY}',
    f'/api/v1/series/{SERIES}/episode/{EP_KEY}',
    f'/_api/series/{SERIES}/{EP_KEY}',
    f'/api/episode/{EP_KEY}',
    f'/api/episode/{EP_KEY}/video',
    f'/api/v1/episode/{EP_KEY}',
    f'/api/v1/play/{SERIES}/{EP_KEY}',
    f'/api/play/{SERIES}/{EP_KEY}',
]
for path in api_paths:
    url = f'https://m.mydramawave.com{path}'
    try:
        r2 = requests.get(url, headers=API_HEADERS, timeout=10)
        if r2.status_code < 500:
            preview = r2.text[:100].replace('\n', ' ')
            print(f'[{r2.status_code}] {path}: {preview}')
    except Exception as e:
        print(f'Error {path}: {e}')
