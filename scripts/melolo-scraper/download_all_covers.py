import os
import requests
from pathlib import Path

def main():
    target_dir = Path(r"D:\kingshortid\Edit Cover")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading Netshort covers to: {target_dir}")
    
    headers = {'Authorization': 'Bearer 00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'}
    r = requests.get('http://localhost:3000/api/dramas?limit=500&includeInactive=true', headers=headers).json()
    
    count = 0
    for d in r.get('dramas', []):
        cover_url = d.get('cover')
        if not cover_url or 'netshort' not in cover_url.lower():
            continue
            
        slug = d['id'] # We'll use the title or slug for easier manual reading
        safe_title = "".join([c for c in d['title'] if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        slug = safe_title.replace(' ', '-').lower()
        
        file_path = target_dir / f"{slug}.jpg"
        
        try:
            img_r = requests.get(cover_url, headers={"User-Agent": "Mozilla/5.0"}, verify=False, timeout=10)
            if img_r.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(img_r.content)
                print(f"Downloaded: {slug}.jpg")
                count += 1
            else:
                print(f"Failed {slug}: HTTP {img_r.status_code}")
        except Exception as e:
            print(f"Error {slug}: {e}")
            
    print(f"\nDone! Downloaded {count} covers to {target_dir.absolute()}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
