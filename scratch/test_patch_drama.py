import requests

session = requests.Session()
login_url = "https://admin.shortlovers.id/api/admin/auth/login"
login_payload = {
    "email": "admin@kingshort.com",
    "password": "admin123"
}

res_login = session.post(login_url, json=login_payload, timeout=10)
print("Login status:", res_login.status_code)

drama_id = "qtfjcm5h28bqklafpgndqxz3"
patch_url = f"https://admin.shortlovers.id/api/dramas/{drama_id}"

# Let's test PATCHing without changing cover first
patch_payload = {
    "title": "(Dub)Sang Bos Naga Kembali",
}

print(f"\nTesting PATCH to {patch_url}...")
try:
    res_patch = session.patch(patch_url, json=patch_payload, timeout=30)
    print("PATCH status:", res_patch.status_code)
    print("PATCH response:", res_patch.text[:200])
except Exception as e:
    print("PATCH error:", e)
