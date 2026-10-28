import requests

session = requests.Session()
login_url = "https://admin.shortlovers.id/api/admin/auth/login"
login_payload = {
    "email": "admin@kingshort.com",
    "password": "admin123"
}

print("1. Logging in...")
res_login = session.post(login_url, json=login_payload, timeout=10)
print("Login status:", res_login.status_code)
print("Cookies:", session.cookies.get_dict())

dummy_content = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xFF\xC0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xFF\xC4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xFF\xDA\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xFF\xD9"

files = {
    'file': ('test_cover.jpg', dummy_content, 'image/jpeg'),
    'folder': (None, 'dramas')
}

upload_url = "https://admin.shortlovers.id/api/upload"
print("\n2. Uploading file to /api/upload...")
try:
    res_upload = session.post(upload_url, files=files, timeout=30)
    print("Upload status:", res_upload.status_code)
    print("Upload response:", res_upload.text)
except Exception as e:
    print("Upload error:", e)
