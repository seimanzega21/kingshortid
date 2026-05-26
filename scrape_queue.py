import os
import sys
import time
import requests

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
VIDRAMA_HDR = {'cookie': '_tt_enable_cookie=1;'}

dramas = [
    {"title": "Dewa Pedang", "bookId": "41000112972", "slug": "dewa-pedang"},
    {"title": "Dewa Masak Cilik", "bookId": "42000000428", "slug": "dewa-masak-cilik"},
    {"title": "Legenda Tangan Dewa", "bookId": "42000011605", "slug": "legenda-tangan-dewa"},
    {"title": "Reinkarnasi Hukum Dewa", "bookId": "42000011638", "slug": "reinkarnasi-hukum-dewa"},
    {"title": "Titisan Dewa Obat", "bookId": "42000011174", "slug": "titisan-dewa-obat"}
]

# Modify scrape_dramabox3 to allow importing and running with parameters
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import scrape_dramabox3

def get_total_eps(book_id):
    # Try finding the highest episode by probing
    # Start checking from 50, if exists check 70, etc. Or just linear search from 1 to 150
    # Actually, linear search is slow but safe.
    last_working = 0
    # Let's do a fast binary search or jump search
    low = 1
    high = 200
    while low <= high:
        mid = (low + high) // 2
        r = requests.get(f'https://vidrama.asia/api/dramabox3/watch?bookId={book_id}&episode={mid}&lang=in', headers=VIDRAMA_HDR)
        if r.ok and r.json().get('success') == True:
            last_working = mid
            low = mid + 1
        else:
            high = mid - 1
            
    # Verification to ensure accuracy
    while True:
        check_ep = last_working + 1
        r = requests.get(f'https://vidrama.asia/api/dramabox3/watch?bookId={book_id}&episode={check_ep}&lang=in', headers=VIDRAMA_HDR)
        if r.ok and r.json().get('success') == True:
            last_working = check_ep
        else:
            break
            
    return last_working

def main():
    print("=" * 60)
    print("STARTING QUEUE SCRAPER")
    print("=" * 60)
    
    for drama in dramas:
        print(f"\n\n>>> PROCESSING: {drama['title']}")
        
        # 1. Check if exists
        r = requests.get(f"{API_BASE}/dramas?limit=1000&includeInactive=true")
        existing = [d for d in r.json().get('data', []) if drama['title'].lower() in d['title'].lower()]
        
        if existing:
            drama_id = existing[0]['id']
            print(f"✓ Found in DB: {drama_id}")
        else:
            # 2. Create in DB
            print(f"Creating {drama['title']} in DB...")
            payload = {
                'title': drama['title'],
                'description': drama['title'],
                'coverImage': 'https://dramaboxdb.com/logo.png',
                'categories': ['Drama'],
                'isActive': False
            }
            res = requests.post(f"{API_BASE}/dramas", headers={'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}, json=payload)
            drama_id = res.json().get('id')
            print(f"✓ Created with ID: {drama_id}")
            
        # 3. Find total eps
        total_eps = get_total_eps(drama['bookId'])
        print(f"✓ Total Episodes: {total_eps}")
        
        if total_eps == 0:
            print(f"✗ Failed to find episodes for {drama['title']}. Skipping.")
            continue
            
        # 4. Override configs in scrape_dramabox3 and run
        scrape_dramabox3.BOOK_ID = drama['bookId']
        scrape_dramabox3.BOOK_SLUG = drama['slug']
        scrape_dramabox3.TOTAL_EPS = total_eps
        scrape_dramabox3.START_EP = 1
        scrape_dramabox3.DRAMA_ID_EXISTING = drama_id
        
        # 5. Run Scraper
        print(f"\nStarting Scraper for {drama['title']}...")
        scrape_dramabox3.main()
        print(f"Finished Scraper for {drama['title']}.")
        
        # Add delay between dramas to prevent bans
        print("Waiting 15 seconds before next drama...")
        time.sleep(15)
        
    print("\nALL QUEUE FINISHED!")

if __name__ == '__main__':
    main()
