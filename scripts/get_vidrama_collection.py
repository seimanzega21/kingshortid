import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_collection():
    cookie = open('vidrama_cookies_final.txt', 'r').read().strip()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Cookie': cookie
    }
    url = "https://vidrama.asia/api/netshortv2/collection/list?page=1&size=50"
    r = requests.get(url, headers=headers, verify=False, timeout=15)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")

if __name__ == "__main__":
    get_collection()
