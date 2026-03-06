import requests, json

r = requests.get('https://vidrama.asia/api/melolo?action=stream&id=7599934467779595269&episode=1', timeout=30)
d = r.json()
data = d.get("data", {})

print("Keys:", list(data.keys()))
proxy_url = data.get("proxyUrl", "")
print("proxyUrl type:", type(proxy_url).__name__)
print("proxyUrl length:", len(proxy_url))

# Write full URL to file for inspection
with open("debug_url.txt", "w") as f:
    f.write(proxy_url)
print("Written to debug_url.txt")

# Show first/last parts
print("First 200 chars:", proxy_url[:200])
print("Last 100 chars:", proxy_url[-100:])
print("Starts with http:", proxy_url.startswith("http"))
