import requests

url = "https://vidrama.asia/watch/dewa-petir-sss-tersembunyi--2089169768653586433/1?provider=netshortv2&lang=id_ID"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

try:
    r = requests.get(url, headers=headers, timeout=10)
    with open('watch.html', 'w', encoding='utf-8') as f:
        f.write(r.text)
    print("Downloaded watch.html")
except Exception as e:
    print(f"Error: {e}")
