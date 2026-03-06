"""
Extract full Supabase anon key and query vidrama drama data.
"""
import requests, re, json, base64

HEADERS = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"}

# Get JS chunk
r = requests.get("https://vidrama.asia/_next/static/chunks/ceb4e2cc20a33317.js", headers=HEADERS, timeout=15)
text = r.text

# Find ALL JWTs with full extraction
jwts = re.findall(r'(eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)', text)
anon_key = None
for jwt in jwts:
    try:
        payload = jwt.split('.')[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        if decoded.get('role') == 'anon':
            anon_key = jwt
            print(f"Anon key found: {len(jwt)} chars")
            print(f"Full key: {jwt}")
            break
    except:
        continue

if not anon_key:
    print("No anon key found!")
    exit()

SUPABASE_URL = "https://gkcnbnlfqdlotnjaizxx.supabase.co"

# User's auth token  
USER_TOKEN = "eyJhbGciOiJFUzI1NiIsImtpZCI6ImY0NTAxYzU1LTY5ZmMtNDczNy05NzFkLTU1OTVjZmRmZDAwNSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2drY25ibmxmcWRsb3RuamFpenh4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJlYjU2MTAwMS0yN2IyLTRlNTctODZlNC1mNjc0NWQwNjQ4YTUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcwNjI5NzEyLCJpYXQiOjE3NzA2MjYxMTIsImVtYWlsIjoiZGF0YWtlcmphMjZAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCIsImdvb2dsZSJdfSwidXNlcl9tZXRhZGF0YSI6eyJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSmRqMGZDamhFcS1jN3pleHFTd05tT185b1I1ampmY1JUMDcxSjd5MndpWGpwWUhnPXM5Ni1jIiwiZW1haWwiOiJkYXRha2VyamEyNkBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZnVsbF9uYW1lIjoiU3VyeWEgSGFsaW0iLCJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJuYW1lIjoiU3VyeWEgSGFsaW0iLCJwaG9uZV92ZXJpZmllZCI6ZmFsc2UsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NKZGowZkNqaEVxLWM3emV4cVN3Tm1PXzlvUjVqamZjUlQwNzFKN3kyd2lYanBZSGc9czk2LWMiLCJwcm92aWRlcl9pZCI6IjEwMDA3MjY1ODAzNjgxMjM1NjExMSIsInN1YiI6IjEwMDA3MjY1ODAzNjgxMjM1NjExMSJ9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6Im9hdXRoIiwidGltZXN0YW1wIjoxNzcwNjIyNTg1fV0sInNlc3Npb25faWQiOiJjMmQ2NTY5Zi0zNmI0LTQzMzEtYmU2Ny05NWJkYTk3ZDk2YTgiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.gkXT2fO0bz81Vc6J5hjZGGW1R5lhmXlEfcYiOm_Mt8P7hRXSsiqrPprH3DXv2PeSzlbtnw-MjviJG4k1q22IXg"

# Try both: anon key and user token
for label, auth_token in [("anon", anon_key), ("user", USER_TOKEN)]:
    print(f"\n=== Trying {label} token ===\n")
    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }
    
    for table in ['dramas', 'drama', 'series', 'novels', 'shows', 'books', 'content', 'provider_content', 'providers', 'episodes', 'chapters']:
        try:
            r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?select=*&limit=1", headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data:
                    print(f"✅ Table '{table}' found! Keys: {list(data[0].keys())}")
                    # Print relevant fields
                    sample = data[0]
                    for field in ['title', 'name', 'cover_url', 'thumbnail', 'poster', 'image_url', 'cover', 'provider']:
                        if field in sample:
                            val = str(sample[field])[:100]
                            print(f"   {field}: {val}")
                else:
                    print(f"  {table}: empty (200)")
            elif r.status_code == 404:
                continue
            else:
                if label == 'anon':
                    continue  # Skip verbose errors for anon
                err = r.text[:100] if r.text else str(r.status_code)
                # Only print first error of each type
                if table == 'dramas':
                    print(f"  {table}: {r.status_code} - {err}")
        except:
            continue
