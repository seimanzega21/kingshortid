import requests
import json
import uuid

API_URL = "https://api.shortlovers.id/api"

# 1. Register a fake user to get a token
email = f"test_{uuid.uuid4().hex[:8]}@example.com"
password = "password123"

print(f"Registering {email}...")
r1 = requests.post(f"{API_URL}/auth/register", json={"email": email, "password": password, "name": "Test User"})
if r1.status_code not in (200, 201):
    print("Register failed:", r1.text)
    exit(1)

token = r1.json().get('token')
print("Got token:", token[:10] + "...")

# 2. Check balance
r2 = requests.get(f"{API_URL}/rewards/status", headers={"Authorization": f"Bearer {token}"})
print("Initial status:", r2.json())

# 3. Call earn-bonus-video
payload = {"type": "checkin_bonus", "amount": 50}
print("Calling earn-bonus-video with payload:", payload)
r3 = requests.post(f"{API_URL}/rewards/earn-bonus-video", json=payload, headers={"Authorization": f"Bearer {token}"})
print("Earn bonus response status:", r3.status_code)
print("Earn bonus response body:", r3.text)

# 4. Check balance again
r4 = requests.get(f"{API_URL}/rewards/status", headers={"Authorization": f"Bearer {token}"})
print("Final status:", r4.json())
