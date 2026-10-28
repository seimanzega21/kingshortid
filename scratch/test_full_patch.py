import requests

session = requests.Session()
login_url = "https://admin.shortlovers.id/api/admin/auth/login"
session.post(login_url, json={"email": "admin@kingshort.com", "password": "admin123"}, timeout=10)

drama_id = "qtfjcm5h28bqklafpgndqxz3"
patch_url = f"https://admin.shortlovers.id/api/dramas/{drama_id}"

# What DramaDetailPage sends when saving:
full_patch_payload = {
    "title": "(Dub)Sang Bos Naga Kembali",
    "description": "Demi kedamaian Kanya, eks bos dunia hitam Karta menyamar dan menikahkan putrinya ke Keluarga Cakra, nahasnya Cakra sang suami malah memaksa Kanya lompat gedung di hari pernikahan, Karta menuntut balas dan menghabisi semua yang melindungi Cakra, tahu putrinya yang koma bisa sadar ia kembali turun gunung demi anaknya",
    "status": "completed",
    "isVip": False,
    "isFeatured": False,
    "genres": ["Drama", "Aksi", "Milliarder", "Sulih Suara"],
    "views": 3199,
    "likes": 1299,
    "rating": 9.6,
    "cover": "https://stream.shortlovers.id/dramas/covers/test_cover.jpg"
}

print("Testing full PATCH payload with genres array...")
try:
    res = session.patch(patch_url, json=full_patch_payload, timeout=10)
    print("Status code:", res.status_code)
    print("Response text:", res.text)
except Exception as e:
    print("Error:", e)
