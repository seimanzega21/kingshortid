"""
Find drama table names by searching vidrama JS chunks for Supabase .from() calls.
"""
import requests, re

HEADERS = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"}

# Get main page to find all JS chunk URLs
r = requests.get("https://vidrama.asia", headers=HEADERS, timeout=15)
# Find ALL script URLs
scripts = re.findall(r'src="(/_next/static/chunks/[^"]+\.js)"', r.text)
print(f"Found {len(scripts)} JS scripts")

# Also look in the provider/melolo page
r2 = requests.get("https://vidrama.asia/provider/melolo", headers=HEADERS, timeout=15)
scripts2 = re.findall(r'src="(/_next/static/chunks/[^"]+\.js)"', r2.text)
# Add unique ones
all_scripts = list(set(scripts + scripts2))
print(f"Total unique scripts: {len(all_scripts)}")

# Search each script for .from("table_name") pattern (Supabase client)
table_names = set()
for i, script_url in enumerate(all_scripts):
    try:
        url = f"https://vidrama.asia{script_url}"
        cr = requests.get(url, headers=HEADERS, timeout=10)
        text = cr.text
        
        # Supabase patterns: .from("table_name"), .from('table_name')
        from_calls = re.findall(r'\.from\(["\']([^"\']+)["\']\)', text)
        if from_calls:
            for t in from_calls:
                table_names.add(t)
                print(f"  {script_url[-25:]}: .from('{t}')")
        
        # Also look for rpc calls
        rpc_calls = re.findall(r'\.rpc\(["\']([^"\']+)["\']\)', text)
        if rpc_calls:
            for t in rpc_calls:
                print(f"  {script_url[-25:]}: .rpc('{t}')")
        
        # Also look for REST API paths
        rest_paths = re.findall(r'/rest/v1/([a-z_]+)', text)
        if rest_paths:
            for t in rest_paths:
                table_names.add(t)
                
    except:
        continue

print(f"\n\n=== All table names found ===")
for t in sorted(table_names):
    print(f"  {t}")
