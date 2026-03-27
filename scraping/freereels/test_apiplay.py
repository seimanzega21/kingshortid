"""Test /api/play/ endpoint with XSRF-TOKEN + full auth"""
import sys, requests, re, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SESSION = 'eyJpdil6lmlI3MDh1WFdzcEZ3Z1FOd2g4a041cVE9PSIsInZhbHVlIjoiTUlCCUzZLcFNYSWVPRU1CNUdvQzhjMStKeE13N0NTZVhMRU8zRVIWQ2tHaUICQm1VcGswd0l5d054Y1ZydTZ6b0JqMTY4U3ZtWWEzUDhCVUYvTjJRa2dDV2hGSy93WnhzVUwxd0VlY1FUR3hBaFJ6bms0Q2NuaHRpTEpsbCs0Z2MiLCJtYWMiOiI2MzhiNWJjNzhjMjY0N2JiZDA4MTJiMTc0OGFhODc2MDM0MzlhOTA5ZjFlNzJkYmZiMWNlYzZmNjlIMWE1OTBkIiwidGFnIjoiln0%3D'
AUTH_PARAMS = '{%22auth_key%22:%220mbsk7VVLt3JLNTqtC1EnJoK0pQAA3pW%22,%22auth_secret%22:%22DjRzZ0PoETLc8K9nq1N89pX2dtvuspc3%22,%22name%22:%22Seiman%20Zega%22,%22user_id%22:36848605951,%22user_type%22:1}'
# XSRF-TOKEN from Application tab (size 352, starts with eyJpdil6JjRo...)
XSRF = 'eyJpdil6JjRoTlZOSlhtdENIbm...'  # partial - need full value

SERIES = 'eNFDnztZRb'
EP_KEY = 'KhuqW30i3V'

# First get the XSRF-TOKEN from cookies
COOKIE = f'_session={SESSION}; auth_params={AUTH_PARAMS}'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'id-ID,id;q=0.9',
    'Referer': f'https://m.mydramawave.com/series/{SERIES}/{EP_KEY}',
    'Cookie': COOKIE,
    'X-Requested-With': 'XMLHttpRequest',
}

# 1. Try GET /api/play/ 
print('=== Testing /api/play/ endpoint ===')
api_url = f'https://m.mydramawave.com/api/play/{SERIES}/{EP_KEY}'
r = requests.get(api_url, headers=HEADERS, timeout=15)
print(f'Status: {r.status_code}')
print(f'Response: {r.text[:500]}')

# 2. Try with XSRF header (from NUXT_DATA flat string seen earlier) 
# Get XSRF from page first
print('\n=== Getting XSRF from page ===')
page = requests.get(f'https://m.mydramawave.com/series/{SERIES}/{EP_KEY}', headers={**HEADERS, 'Accept': 'text/html'}, timeout=15)
# Check if response has XSRF cookie
print('Response cookies:', dict(page.cookies))
xsrf = page.cookies.get('XSRF-TOKEN', '')
print(f'XSRF from response cookies: {xsrf[:80]}')

if xsrf:
    h2 = {**HEADERS, 'X-XSRF-TOKEN': xsrf}
    r2 = requests.get(api_url, headers=h2, timeout=15)
    print(f'\nWith XSRF - Status: {r2.status_code}')
    print(f'Response: {r2.text[:500]}')
