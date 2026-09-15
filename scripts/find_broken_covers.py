import json
import requests
import concurrent.futures
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
import urllib3
urllib3.disable_warnings()

with open('all_dramas_for_scan.json', 'r', encoding='utf-8') as f:
    dramas = json.load(f)

session = requests.Session()
adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=1)
session.mount('https://', adapter)
session.mount('http://', adapter)

broken_dramas = []
checked = 0

def check_drama(d):
    cover = d.get('cover', '').strip()
    if not cover or not cover.startswith('http'):
        return (d, 0, 'EMPTY_OR_INVALID')
    try:
        r = session.head(cover, timeout=6, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code != 200:
            return (d, r.status_code, 'NOT_200')
        # Also check content type if available
        ct = r.headers.get('content-type', '').lower()
        if 'text/html' in ct or 'application/json' in ct:
            return (d, r.status_code, 'HTML_ERROR_PAGE')
        return None
    except Exception as e:
        return (d, 0, str(e)[:50])

print(f"Checking {len(dramas)} drama covers...")
with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
    futures = [executor.submit(check_drama, d) for d in dramas]
    for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
        res = fut.result()
        if res is not None:
            drama, status, reason = res
            broken_dramas.append({
                'id': drama['id'],
                'title': drama['title'],
                'cover': drama['cover'],
                'status': status,
                'reason': reason
            })
        if i % 200 == 0 or i == len(dramas):
            print(f"Progress: {i}/{len(dramas)} checked | Found broken: {len(broken_dramas)}")

print(f"\nScan complete! Found {len(broken_dramas)} dramas with broken/404 covers.")
with open('broken_covers.json', 'w', encoding='utf-8') as f:
    json.dump(broken_dramas, f, indent=2, ensure_ascii=False)
