import urllib3
import sys
import requests
import time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download(url, out_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "identity;q=1, *;q=0",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Range": "bytes=0-",
        "Referer": "https://vidrama.asia/",
        "Sec-Fetch-Dest": "video",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site"
    }
    
    try:
        print(f"Downloading with spoofed headers...")
        r = requests.get(url, headers=headers, stream=True, timeout=60, verify=False)
        r.raise_for_status()
        
        with open(out_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk: f.write(chunk)

                
        import os
        sz = os.path.getsize(out_path)
        if sz > 1024 * 1024:
            print(f"SUCCESS {out_path}")
        else:
            print(f"ERROR File too small ({sz} bytes)")
    except Exception as e:
        print(f"ERROR {e}")
        sys.exit(1)

if __name__ == "__main__":
    url = sys.argv[1]
    out = sys.argv[2]
    download(url, out)
