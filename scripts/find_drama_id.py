import requests
import json
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def find_drama(title_part):
    cookie = open('vidrama_cookies_final.txt', 'r').read().strip()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Cookie': cookie
    }
    
    for page in range(1, 10):
        print(f"Checking page {page}...")
        url = f"https://vidrama.asia/api/netshortv2/list?page={page}&size=50&lang=id_ID"
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=15)
            if r.status_code != 200:
                print(f"  Error {r.status_code}")
                continue
            
            data = r.json()
            if data.get('code') != 200:
                print(f"  API Error: {data.get('msg')}")
                continue
                
            dramas = data.get('data', {}).get('list', [])
            if not dramas:
                print("  No more dramas.")
                break
                
            for d in dramas:
                if title_part.lower() in d.get('title', '').lower():
                    print(f"FOUND: {d['id']} | {d['title']} | {d.get('slug')}")
                    return d['id']
        except Exception as e:
            print(f"  Exception: {e}")
        time.sleep(1)
    return None

if __name__ == "__main__":
    find_drama("Wanita Jenius")
