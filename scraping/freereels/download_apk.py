"""Download FreeReels APK from APKPure/APKCombo"""
import requests, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://apkpure.com/',
}

def try_download(url, out_file):
    print(f'Trying: {url}')
    try:
        r = requests.get(url, headers=headers, stream=True, allow_redirects=True, timeout=60)
        print(f'  Status: {r.status_code}, Content-Type: {r.headers.get("content-type","?")}')
        if r.status_code == 200:
            ct = r.headers.get('content-type', '')
            if 'apk' in ct or 'zip' in ct or 'octet-stream' in ct or r.headers.get('content-length','0') > '100000':
                with open(out_file, 'wb') as f:
                    total = 0
                    for chunk in r.iter_content(chunk_size=65536):
                        f.write(chunk)
                        total += len(chunk)
                size = os.path.getsize(out_file)
                if size > 1_000_000:
                    print(f'  Downloaded: {size/1024/1024:.1f} MB -> {out_file}')
                    return True
                else:
                    os.remove(out_file)
                    print(f'  Too small: {size} bytes')
            else:
                print(f'  Not an APK response')
        return False
    except Exception as e:
        print(f'  Error: {e}')
        return False

# Try multiple sources
sources = [
    'https://d.apkpure.com/b/APK/com.freereels.app?version=latest',
    'https://d.apkpure.com/b/APK/com.freereels.app?version=2.2.10',
    'https://apkpure.com/freereels-dramas-reels/com.freereels.app/APK',
]

out = 'freereels.apk'
for url in sources:
    if try_download(url, out):
        print(f'\nSUCCESS! APK saved to {out}')
        print('Now run: npx apk-mitm freereels.apk')
        break
else:
    print('\nAll sources failed. Manual download needed.')
    print('Open: https://apkpure.com/freereels-dramas-reels/com.freereels.app')
    print('Click Download APK, save to: d:/kingshortid/scraping/freereels/freereels.apk')
