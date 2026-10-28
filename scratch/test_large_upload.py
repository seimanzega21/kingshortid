import requests
import time

session = requests.Session()
login_url = "https://admin.shortlovers.id/api/admin/auth/login"
session.post(login_url, json={"email": "admin@kingshort.com", "password": "admin123"}, timeout=10)

# Create a 3MB dummy image
content_3mb = b"\xFF\xD8\xFF\xE0" + (b"\x00" * (3 * 1024 * 1024)) + b"\xFF\xD9"

files = {
    'file': ('test_3mb.jpg', content_3mb, 'image/jpeg'),
    'folder': (None, 'dramas')
}

upload_url = "https://admin.shortlovers.id/api/upload"
print("Uploading 3MB file...")
t0 = time.time()
try:
    res = session.post(upload_url, files=files, timeout=60)
    print(f"Status in {time.time()-t0:.2f}s:", res.status_code)
    print("Response:", res.text)
except Exception as e:
    print(f"Error in {time.time()-t0:.2f}s:", e)

# Create a 7MB dummy image
content_7mb = b"\xFF\xD8\xFF\xE0" + (b"\x00" * (7 * 1024 * 1024)) + b"\xFF\xD9"
files = {
    'file': ('test_7mb.jpg', content_7mb, 'image/jpeg'),
    'folder': (None, 'dramas')
}
print("\nUploading 7MB file...")
t0 = time.time()
try:
    res = session.post(upload_url, files=files, timeout=60)
    print(f"Status in {time.time()-t0:.2f}s:", res.status_code)
    print("Response:", res.text)
except Exception as e:
    print(f"Error in {time.time()-t0:.2f}s:", e)
