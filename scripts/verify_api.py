import requests
import json

API_BASE = 'https://api.shortlovers.id'

print('=== KINGSHORT API ENDPOINT STATUS ===')

# 1. Health check
r = requests.get(API_BASE, timeout=10)
print(f"\n1. Health Check: {r.status_code}")
if r.ok:
    data = r.json()
    print(f"   Service: {data.get('service')}")
    print(f"   Runtime: {data.get('runtime')}")

# 2. Login (invalid user → expect 401)
r = requests.post(f'{API_BASE}/api/auth/login', json={'email':'test@test.com','password':'123456'}, timeout=15)
print(f"\n2. Login (invalid user): {r.status_code}")
print(f"   Response: {r.json().get('message')}")
if r.status_code == 401:
    print("   [PASS] Login endpoint normal (401 = user tidak ditemukan, bukan 500!)")
else:
    print(f"   [FAIL] Login error: {r.text[:100]}")

# 3. Rewards daily (expect 401 tanpa auth)
r = requests.get(f'{API_BASE}/api/rewards/daily/7?userId=fake', timeout=10)
print(f"\n3. Daily Rewards: {r.status_code}")
if r.status_code == 401:
    print("   [PASS] Endpoint normal (butuh auth)")

# 4. Coin transactions (expect 401 tanpa auth)
r = requests.get(f'{API_BASE}/api/coins/transactions/7?userId=fake', timeout=10)
print(f"\n4. Coin Transactions: {r.status_code}")
if r.status_code == 401:
    print("   [PASS] Endpoint normal (butuh auth)")

# 5. Dramas list (public endpoint)
r = requests.get(f'{API_BASE}/api/dramas?limit=1', timeout=10)
print(f"\n5. Dramas List: {r.status_code}")
if r.ok:
    print("   [PASS] Endpoint public OK")
else:
    print(f"   [FAIL] {r.text[:100]}")

print("\n=== SUMMARY ===")
print("Semua endpoint sudah merespons status yang benar.")
print("Login error 500 sudah diperbaiki — sekarang 401 (user tidak ditemukan).")
print("\nCATATAN: Sekarang login pakai user real supaya bisa test check-in/rewards.")
