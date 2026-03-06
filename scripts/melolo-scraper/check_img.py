import requests

r = requests.get('https://stream.shortlovers.id/melolo/kebangkitan-dewi-giok/poster.jpg', timeout=10)
data = r.content
print(f"Size: {len(data)} bytes")
print(f"First 4 bytes (hex): {data[:4].hex()}")

if data[:3] == bytes([0xFF, 0xD8, 0xFF]):
    print("Format: JPEG ✅")
else:
    print(f"Format: NOT JPEG ❌")
