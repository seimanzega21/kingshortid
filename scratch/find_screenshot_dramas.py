import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; global_ui_lang=id; cf_clearance=gi8rBDL4U_sV5dFUP.Dckjr.DONUzFar9fJlBMJx5_c-1778228148-1.2.1.1-rcSC4qbKF5H0KxB5Zt6Ic88iCIyXH7DESdcJA5w9WLWZvk58Y70clfcHFfqOyxmSRb1I97eRy.96PRr0zF1vV_PWs7vWkLZg2IsJNYLl5ZJvxdv7AnK4pZgxEBspgbrAod7jxce171vMiENcKPDXk_1eVFpBk_P5H8TA07xIBdq5HsL3uPTZKn8BCJv.HufjCR4mRr3DVOGDRagaNcc1CD_VmnRYY6tkanYH9QuDUyPeqreywRNxjb_5tsJVseZjz24po7Gw9o9ZVi3mSl9Ypm88Po1s4zr5n3DfE5R4BCKekPgqBAog2SDMQmDCWQJjMpzKKsJ_iXUHRaincYv9WQ'
}

PINE_API = 'https://vidrama.asia/api/pine'

# IDs extracted from the screenshot:
# - URL bar shows: tiga-istri-untuk-sang-praju...--7646413641771176380 (partial)
# - drama: sang-juara-menyamar-jadi-ob--7643677444247311367 (from original URL user shared)
# Let's check specific IDs visible from URLs/patterns in the screenshot
# and also do targeted searches for each title seen

# Try direct ID lookups for dramas visible in screenshot
candidate_ids = [
    # From URL in status bar of screenshot
    '7646413641771176380',  # Tiga istri untuk sang prajurit (visible in status bar)
    # Common Pine drama IDs pattern (sequential, from screenshot context)
    '7643677444247311367',  # Sang juara menyamar jadi OB (user's original URL)
]

# Also search for exact titles from screenshot
from_screenshot_searches = [
    'Dendam kesatria terakhir',
    'Master tenis meja tersembunyi',
    'Dokter Hewan Para Raja Iblis',
    'Balas dendam sang raja tinju',
    'Putri sakti jadi peramal',
    'Sang jagoan jalanan',
    'Evolusi ular pemangsa',
    'Sang Raja Dewa',
    'Kebangkitan Raja Kera',
    'Suamiku sang Raja Asura',
    'Dendam Sang Master',
    'Relik yang hilang memanggil ibu',
]

print("=== CHECKING CANDIDATE IDs ===")
verified = {}
for did in candidate_ids:
    r = requests.get(f'{PINE_API}?action=detail&collection_id={did}', headers=headers, verify=False, timeout=10)
    if r.ok and r.json().get('title'):
        data = r.json()
        title = data['title']
        eps = data.get('totalEpisodes', '?')
        print(f"  OK [{did}] {title} ({eps} ep)")
        verified[did] = title
    else:
        print(f"  ERR [{did}] -> {r.status_code}: {r.text[:100]}")

print("\n=== SEARCHING BY EXACT TITLE ===")
all_results = {}
for title in from_screenshot_searches:
    # Try keyword search - use just first 2 words for more targeted results
    words = title.split()[:2]
    query = ' '.join(words)
    r = requests.get(f'{PINE_API}?action=search&keyword={query}', headers=headers, verify=False, timeout=10)
    if r.ok:
        dramas = r.json().get('dramas', [])
        # Find exact or close match
        for d in dramas:
            d_title_lower = d['title'].lower()
            search_lower = title.lower()
            # Check if significant words match
            match_words = [w for w in title.lower().split() if len(w) > 3 and w in d_title_lower]
            if len(match_words) >= 2 or search_lower in d_title_lower or d_title_lower in search_lower:
                did = d['id']
                if did not in all_results:
                    print(f"  [{did}] {d['title']} (search: '{title}')")
                    all_results[did] = d['title']

print(f"\nTotal unique new dramas found: {len(all_results)}")
print("\n=== FINAL LIST FOR SCRAPER ===")
for did, title in all_results.items():
    print(f'    {{"id": "{did}", "title": "{title}"}},')
