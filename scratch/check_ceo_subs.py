import requests

url = "https://vidrama.asia/api/dramabox3/proxy?url=https%3A%2F%2Fhwztvideo.dramaboxdb.com%2F68%2F2x5%2F25x9%2F259x4%2F25940000024%2F700320486_19_sub%2Fin.srt"

print(f"Requesting subtitle URL: {url}\n")
try:
    r = requests.get(url, timeout=15)
    print(f"HTTP Status Code: {r.status_code}")
    print(f"Content Type: {r.headers.get('Content-Type')}")
    print(f"Content Length: {len(r.content)} bytes")
    print("\nFirst 300 characters of response:")
    print("=" * 40)
    print(r.text[:300])
    print("=" * 40)
except Exception as e:
    print(f"Error fetching URL: {e}")
