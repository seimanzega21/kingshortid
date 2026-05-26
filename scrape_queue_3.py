import os
import sys
import time
import requests

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
VIDRAMA_HDR = {'cookie': '_tt_enable_cookie=1;'}

dramas = [
    {"title": "Pedang Sakti Sang Menantu Desa", "bookId": "42000011187", "slug": "pedang-sakti-sang-menantu-desa"}
]

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import scrape_dramabox3

def get_total_eps(book_id):
    last_working = 0
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
    print("STARTING QUEUE SCRAPER 3")
    print("=" * 60)
    
    for drama in dramas:
        print(f"\n\n>>> PROCESSING: {drama['title']}")
        
        r = requests.get(f"{API_BASE}/dramas?limit=1000&includeInactive=true")
        existing = [d for d in r.json().get('data', []) if drama['title'].lower() in d['title'].lower()]
        
        if existing:
            drama_id = existing[0]['id']
            print(f"✓ Found in DB: {drama_id}")
        else:
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
            
        total_eps = get_total_eps(drama['bookId'])
        print(f"✓ Total Episodes: {total_eps}")
        
        if total_eps == 0:
            print(f"✗ Failed to find episodes for {drama['title']}. Skipping.")
            continue
            
        scrape_dramabox3.BOOK_ID = drama['bookId']
        scrape_dramabox3.BOOK_SLUG = drama['slug']
        scrape_dramabox3.TOTAL_EPS = total_eps
        scrape_dramabox3.START_EP = 1
        scrape_dramabox3.DRAMA_ID_EXISTING = drama_id
        
        print(f"\nStarting Scraper for {drama['title']}...")
        scrape_dramabox3.main()
        print(f"Finished Scraper for {drama['title']}.")
        
        print("Waiting 15 seconds before next drama...")
        time.sleep(15)
        
    print("\nALL QUEUE FINISHED!")

if __name__ == '__main__':
    main()
