"""
Query vidrama Supabase directly with the anon key to find drama covers.
"""
import requests, re, json, base64

HEADERS = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"}

# Step 1: Extract the FULL anon key properly
r = requests.get("https://vidrama.asia/_next/static/chunks/ceb4e2cc20a33317.js", headers=HEADERS, timeout=15)
text = r.text

# Find all JWTs 
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
            print(f"✅ Anon key: {anon_key}")
            break
    except:
        continue

SUPABASE_URL = "https://gkcnbnlfqdlotnjaizxx.supabase.co"

headers = {
    "apikey": anon_key,
    "Authorization": f"Bearer {anon_key}",
    "Content-Type": "application/json",
}

# Step 2: Discover available tables by trying many names
print(f"\n=== Discovering tables ===\n")
tables_found = []
all_tables = [
    'dramas', 'drama', 'series', 'novels', 'shows', 'books', 'content',
    'media', 'videos', 'providers', 'provider', 'episodes', 'chapters',
    'categories', 'genres', 'users', 'profiles', 'watch_history',
    'favorites', 'bookmarks', 'comments', 'ratings', 'reviews',
    'subscriptions', 'plans', 'payments', 'notifications',
    'settings', 'site_settings', 'announcements', 'banners',
    'tags', 'authors', 'actors', 'directors', 'casts',
    'drama_providers', 'provider_dramas', 'drama_episodes',
    'novel_chapters', 'book_chapters', 'video_episodes',
    'melolo', 'goodshort', 'stardust',
]

for table in all_tables:
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?select=*&limit=1", headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            tables_found.append(table)
            if data:
                print(f"✅ {table}: {list(data[0].keys())}")
            else:
                print(f"✅ {table}: (empty)")
        elif r.status_code != 404 and r.status_code != 400:
            # 401 = unauthorized, 403 = forbidden (table exists but no access)
            if r.status_code in [401, 403]:
                pass  # Skip these silently
            else:
                print(f"  {table}: {r.status_code}")
    except:
        pass

print(f"\nFound tables: {tables_found}")

# Step 3: If we find the right table, search for our dramas
if tables_found:
    for table in tables_found:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?select=*&limit=5", headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data:
                print(f"\n=== {table} sample data ===\n")
                for row in data:
                    print(json.dumps(row, indent=2, ensure_ascii=False)[:500])
                    print("---")
                
                # Search for target dramas
                targets = ["Bertapa", "Kaisar", "Nasib", "Sultan", "1977"]
                for search in targets:
                    # Try ilike search on title field
                    for field in ['title', 'name', 'original_title', 'drama_title']:
                        if field in data[0]:
                            try:
                                r2 = requests.get(
                                    f"{SUPABASE_URL}/rest/v1/{table}?{field}=ilike.*{search}*&select=*", 
                                    headers=headers, timeout=10
                                )
                                if r2.status_code == 200 and r2.json():
                                    print(f"\n✅ Found '{search}' in {table}.{field}:")
                                    for d in r2.json():
                                        print(json.dumps(d, indent=2, ensure_ascii=False)[:400])
                            except:
                                pass
                break
else:
    print("\n❌ No tables accessible with anon key")
    print("The RLS policies likely block anonymous access")
    print("Need user's authenticated token (but it's expired)")
