"""Try to find and download FreeReels APK from multiple sources"""
import requests, re, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36'}

def try_direct_dl(url, out):
    try:
        r = requests.get(url, headers=H, stream=True, allow_redirects=True, timeout=60)
        print(f'  {r.status_code} {r.headers.get("content-type","?")} @ {r.url[:80]}')
        if r.status_code == 200:
            ct = r.headers.get('content-type','')
            size_hint = int(r.headers.get('content-length','0'))
            if size_hint > 1_000_000 or 'octet' in ct or 'zip' in ct:
                with open(out, 'wb') as f:
                    total = 0
                    for chunk in r.iter_content(65536):
                        f.write(chunk); total += len(chunk)
                if os.path.getsize(out) > 1_000_000:
                    print(f'  OK: {os.path.getsize(out)/1024/1024:.1f} MB')
                    return True
                os.remove(out)
    except Exception as e:
        print(f'  Error: {e}')
    return False

# Try APKCombo
print('=== APKCombo ===')
r = requests.get('https://apkcombo.com/freereels-dramas-reels/com.freereels.app/download/apk', headers=H, timeout=20)
print(f'Status: {r.status_code}')
# Find download URLs
links = re.findall(r'href=["\']([^"\']*?com\.freereels[^"\']*?)["\']', r.text)
print(f'Links found: {links[:5]}')
dl_links = re.findall(r'(https?://[^\s"\'<>]*?\.(?:apk|xapk)[^\s"\'<>]*)', r.text)
print(f'Direct APK links: {dl_links[:5]}')

# Also search for any download href
all_dl = re.findall(r'href=["\']([^"\']*?download[^"\']*?)["\']', r.text)
print(f'Download hrefs: {all_dl[:10]}')
