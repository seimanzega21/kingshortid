import requests, sys, json
sys.stdout.reconfigure(encoding="utf-8")
token = "XkVu-X5XTL0_fBrkYcYANLpOZlSJxFKuyXYtTSYw"

# Verify token
r = requests.get(
    "https://api.cloudflare.com/client/v4/user/tokens/verify",
    headers={"Authorization": f"Bearer {token}"},
    timeout=10
)
print("Token verify:", r.status_code, json.dumps(r.json().get("result", {})))

# Get zones
r2 = requests.get(
    "https://api.cloudflare.com/client/v4/zones",
    headers={"Authorization": f"Bearer {token}"},
    timeout=10
)
data = r2.json()
print("Zones HTTP:", r2.status_code)
for z in data.get("result", []):
    print(f"Zone: {z['name']} | ID: {z['id']}")
if not data.get("result"):
    print("No zones found:", json.dumps(data.get("errors", [])))
