import requests

# Test several URL patterns
urls = [
    "https://stream.shortlovers.id/freereels/bertahan_hidup_di_sekolah_elit/ep_002.mp4",
    "https://stream.shortlovers.id/freereels/a_mother_wont_hold_back/ep_001.mp4",
]

for url in urls:
    try:
        r = requests.head(url, timeout=10, allow_redirects=True)
        print(f"{r.status_code} | {r.headers.get('content-type','?')[:20]} | {int(r.headers.get('content-length',0))/1024/1024:.1f}MB | {url[-50:]}")
    except Exception as e:
        print(f"ERR | {e} | {url[-50:]}")

# Also check a known GoodShort URL that works
known_url = "https://stream.shortlovers.id/goodshort/"
try:
    r2 = requests.head(known_url, timeout=10, allow_redirects=True)
    print(f"\nGoodShort prefix: {r2.status_code}")
except Exception as e:
    print(f"\nGoodShort prefix: ERR {e}")
