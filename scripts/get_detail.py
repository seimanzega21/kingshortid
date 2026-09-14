import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(
    'https://vidrama.asia/api/netshortv2/detail/2096782583337111554?lang=id_ID',
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
)

try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as res:
        data = json.loads(res.read().decode('utf-8'))
        print("HTTP Status:", res.status)
        print("API Code:", data.get('code'))
        d = data.get('data', {})
        print("Title:", d.get('title'))
        print("Total Episodes:", d.get('totalEpisodes'))
        print("Cover:", d.get('cover'))
        with open('scripts/desainer_detail.json', 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        print("Saved to scripts/desainer_detail.json")
except Exception as e:
    print("Error:", e)
