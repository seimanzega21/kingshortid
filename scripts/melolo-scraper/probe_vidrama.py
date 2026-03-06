"""
Probe vidrama.asia API to find cover images for 5 dramas.
Uses Supabase backend extracted from JWT token.
"""
import requests, json

TOKEN = "eyJhbGciOiJFUzI1NiIsImtpZCI6ImY0NTAxYzU1LTY5ZmMtNDczNy05NzFkLTU1OTVjZmRmZDAwNSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2drY25ibmxmcWRsb3RuamFpenh4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJlYjU2MTAwMS0yN2IyLTRlNTctODZlNC1mNjc0NWQwNjQ4YTUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcwNjI5NzEyLCJpYXQiOjE3NzA2MjYxMTIsImVtYWlsIjoiZGF0YWtlcmphMjZAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCIsImdvb2dsZSJdfSwidXNlcl9tZXRhZGF0YSI6eyJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSmRqMGZDamhFcS1jN3pleHFTd05tT185b1I1ampmY1JUMDcxSjd5MndpWGpwWUhnPXM5Ni1jIiwiZW1haWwiOiJkYXRha2VyamEyNkBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZnVsbF9uYW1lIjoiU3VyeWEgSGFsaW0iLCJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJuYW1lIjoiU3VyeWEgSGFsaW0iLCJwaG9uZV92ZXJpZmllZCI6ZmFsc2UsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NKZGowZkNqaEVxLWM3emV4cVN3Tm1PXzlvUjVqamZjUlQwNzFKN3kyd2lYanBZSGc9czk2LWMiLCJwcm92aWRlcl9pZCI6IjEwMDA3MjY1ODAzNjgxMjM1NjExMSIsInN1YiI6IjEwMDA3MjY1ODAzNjgxMjM1NjExMSJ9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6Im9hdXRoIiwidGltZXN0YW1wIjoxNzcwNjIyNTg1fV0sInNlc3Npb25faWQiOiJjMmQ2NTY5Zi0zNmI0LTQzMzEtYmU2Ny05NWJkYTk3ZDk2YTgiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.gkXT2fO0bz81Vc6J5hjZGGW1R5lhmXlEfcYiOm_Mt8P7hRXSsiqrPprH3DXv2PeSzlbtnw-MjviJG4k1q22IXg"

SUPABASE_URL = "https://gkcnbnlfqdlotnjaizxh.supabase.co"
# Supabase anon key is usually public - try to get it from the site
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdrY25ibmxmcWRsb3RuamFpenh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzcwMjYzOTQsImV4cCI6MjA1MjYwMjM5NH0.gA_JRPrIGiElbFHytzMMjU2hk2N5lYDqMcRMwWKGcUE"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "apikey": ANON_KEY,
    "Content-Type": "application/json",
}

TARGET_DRAMAS = [
    "Setelah Bertapa, Kutaklukkan Dunia",
    "Siapa yang Sedang Membicarakan Kaisar",
    "Sistem Perubah Nasib",
    "Sistem Suami Sultan",
    "Tahun 1977 Penuh Peluang",
]

# Try 1: Direct Supabase REST - search dramas table
print("=== Probing Supabase REST API ===\n")

# Try common table names
for table in ['dramas', 'drama', 'series', 'novels', 'content', 'videos']:
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?select=*&limit=1", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Table '{table}' found! ({len(data)} rows)")
            if data:
                print(f"   Fields: {list(data[0].keys())}")
                print(f"   Sample: {json.dumps(data[0], indent=2, ensure_ascii=False)[:500]}")
            break
        elif r.status_code == 404:
            continue
        else:
            print(f"  {table}: {r.status_code}")
    except Exception as e:
        print(f"  {table}: {e}")

# Try 2: Search via the vidrama.asia website's own API
print("\n\n=== Probing vidrama.asia API ===\n")

for prefix in ['/api', '/_next/data']:
    for endpoint in ['/dramas', '/search', '/provider/melolo', '/series']:
        url = f"https://vidrama.asia{prefix}{endpoint}"
        try:
            r = requests.get(url, headers={"Authorization": f"Bearer {TOKEN}"}, timeout=10)
            print(f"  {url}: {r.status_code} ({r.headers.get('content-type', '')[:30]})")
            if r.status_code == 200 and 'json' in r.headers.get('content-type', ''):
                data = r.json()
                print(f"    Keys: {list(data.keys()) if isinstance(data, dict) else f'{len(data)} items'}")
                if isinstance(data, list) and len(data) > 0:
                    print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:300]}")
                break
        except:
            continue

# Try 3: Supabase RPC functions 
print("\n\n=== Trying Supabase RPC ===\n")
for fn in ['search_dramas', 'get_dramas', 'get_provider_dramas']:
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/{fn}", 
            headers=HEADERS, 
            json={"query": "Bertapa", "provider": "melolo"},
            timeout=10)
        if r.status_code != 404:
            print(f"  {fn}: {r.status_code}")
            if r.status_code == 200:
                print(f"    {json.dumps(r.json(), ensure_ascii=False)[:500]}")
            elif r.text:
                print(f"    {r.text[:200]}")
    except:
        pass

# Try 4: Search the vidrama search page
print("\n\n=== Trying vidrama search ===\n")
for drama in TARGET_DRAMAS[:1]:
    # Try the search endpoint
    term = drama.split(',')[0].strip()[:20]
    try:
        r = requests.get(f"https://vidrama.asia/search?q={term}", timeout=10)
        print(f"  Search '{term}': {r.status_code} ({len(r.text)} bytes)")
    except Exception as e:
        print(f"  Error: {e}")
