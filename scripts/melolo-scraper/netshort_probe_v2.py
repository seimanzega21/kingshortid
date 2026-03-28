#!/usr/bin/env python3
"""
NETSHORT API PROBE v2 — Using JWT Auth Token
============================================
Gunakan Supabase JWT dari browser session untuk:
1. Test Supabase REST API → list drama Netshort
2. Test Vidrama Next.js API → get episode video URLs
3. Find next-action token dari JS bundle
"""
import requests, json, re, time
from pathlib import Path

# ─── TOKEN CONFIG (dari browser localStorage) ───
ACCESS_TOKEN  = "eyJhbGciOiJFUzI1NiIsImtpZCI6ImY0NTAxYzU1LTY5ZmMtNDczNy05NzFkLTU1OTVjZmRmZDAwNSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2drY25ibmxmcWRsb3RuamFpenh4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI2ZjNlNWMxNS1hMjFjLTRkMTAtYjg2Yy1lODgxNzBlN2I3MmQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc0NjkzMzkxLCJpYXQiOjE3NzQ2ODk3OTEsImVtYWlsIjoic2VpbWFuemVnYTIxQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSIsImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImF2YXRhcl91cmwiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NLTHVLNzltN2xuOWdBcXJRVEhNVFFDZTFRR3B3Vy10dHh2RW1lNWUzSTF2OHBubGpvPXM5Ni1jIiwiZW1haWwiOiJzZWltYW56ZWdhMjFAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6InNlaW1hbiB6ZWdhIiwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tIiwibmFtZSI6InNlaW1hbiB6ZWdhIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jS0x1Szc5bTdsbjlnQXFyUVRITVRRQ2UxUUdwd1ctdHR4dkVtZTVlM0kxdjhwbmxqbz1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA3NjA4MDAzMDIzNjk0ODg5MzE3Iiwic3ViIjoiMTA3NjA4MDAzMDIzNjk0ODg5MzE3In0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NzQ2ODk3OTF9XSwic2Vzc2lvbl9pZCI6ImE0NTM5MWFjLWM4YWItNDI3ZC05OTNkLWFhZDYxMjI0MTJlYyIsImlzX2Fub255bW91cyI6ZmFsc2V9.V3BqHWPqGHVkkE9Sqb4IOJcPO51ZblyWk_oZbfyJgP1y9dh_HUV4Snd_AKkEoeWLELPlEcjpLSIu6OP7Q9K-kw"
REFRESH_TOKEN = "l35sdnbtaykg"
SUPABASE_URL  = "https://gkcnbnlfqdlotnjaizxx.supabase.co"
SUPABASE_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdrb25ibmxmcWRsb3RuamFpenh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk4NTc3MjIsImV4cCI6MjA1NTQzMzcyMn0.hmGhevXYhqRxfHOQxRCfMsMNJuOBdRPWHbmIXNcJxVo"
VIDRAMA_BASE  = "https://vidrama.asia"

# Known drama IDs from sessionStorage
SAMPLE_DRAMAS = [
    {"id": "2033755298681847810", "slug": "si-jenius-tak-sadar-diri", "title": "Si Jenius Tak Sadar Diri"},
    {"id": "2034897075744800770", "slug": "gejolak-keluarga-konglomerat", "title": "Gejolak Keluarga Konglomerat"},
    {"id": "2033496357230084097", "slug": "melawan-dewa-ribuan-tahun", "title": "Melawan Dewa Ribuan Tahun"},
]

def get_auth_headers():
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

def refresh_access_token():
    """Refresh the Supabase JWT token using refresh_token."""
    print("[TOKEN] Refreshing access token...")
    r = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
        json={"refresh_token": REFRESH_TOKEN},
        headers={"apikey": SUPABASE_ANON, "Content-Type": "application/json"},
        timeout=15
    )
    if r.status_code == 200:
        data = r.json()
        new_access = data.get("access_token", "")
        new_refresh = data.get("refresh_token", REFRESH_TOKEN)
        print(f"  ✅ New token (exp: {data.get('expires_in', 0)}s)")
        return new_access, new_refresh
    else:
        print(f"  ❌ Refresh failed: {r.status_code} {r.text[:100]}")
        return ACCESS_TOKEN, REFRESH_TOKEN


def test_supabase_rest():
    """Try to get Netshort drama list from Supabase REST API."""
    print("\n=== [1] Supabase REST API ===")
    tables = ["movies", "short_plays", "dramas", "videos", "drama", "content"]
    for table in tables:
        url = f"{SUPABASE_URL}/rest/v1/{table}?provider=eq.netshort&limit=5"
        hdrs = {
            **get_auth_headers(),
            "apikey": SUPABASE_ANON,
            "Prefer": "return=representation",
        }
        try:
            r = requests.get(url, headers=hdrs, timeout=10)
            if r.status_code == 200:
                data = r.json()
                print(f"  ✅ Table '{table}': {len(data)} rows")
                if data:
                    print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:200]}")
            else:
                print(f"  ❌ Table '{table}': {r.status_code}")
        except Exception as e:
            print(f"  ❌ Table '{table}': {e}")


def test_vidrama_api():
    """Try various Vidrama API endpoints for Netshort drama list."""
    print("\n=== [2] Vidrama API Endpoints ===")
    endpoints = [
        f"{VIDRAMA_BASE}/api/netshort?action=list&lang=id&limit=10",
        f"{VIDRAMA_BASE}/api/netshort?action=search&keyword=a&limit=10",
        f"{VIDRAMA_BASE}/api/movies?provider=netshort&limit=10",
        f"{VIDRAMA_BASE}/api/dramas?provider=netshort&limit=10",
    ]
    for url in endpoints:
        try:
            r = requests.get(url, headers=get_auth_headers(), timeout=10)
            print(f"  [{r.status_code}] {url.split('vidrama.asia')[1][:60]}")
            if r.status_code == 200:
                print(f"    Response: {r.text[:200]}")
        except Exception as e:
            print(f"  [ERR] {url}: {e}")


def find_next_action_token():
    """Scan Next.js JS bundles to find server action IDs for Netshort."""
    print("\n=== [3] Finding next-action token from JS bundles ===")
    # Get the main page to find chunk URLs
    try:
        r = requests.get(f"{VIDRAMA_BASE}/provider/netshort", timeout=15, headers={
            "User-Agent": "Mozilla/5.0",
        })
        # Find all JS chunk URLs
        chunks = re.findall(r"/_next/static/chunks/[^\"'\s]+\.js", r.text)
        print(f"  Found {len(chunks)} JS chunks")

        # Search relevant chunks for server action hashes
        for chunk in chunks[:20]:
            chunk_url = f"{VIDRAMA_BASE}{chunk}"
            try:
                cj = requests.get(chunk_url, timeout=10)
                if cj.status_code == 200:
                    # Look for server action hashes near "netshort" keyword
                    text = cj.text
                    if "netshort" in text.lower():
                        # Find 40-char hex hashes near "netshort"
                        matches = re.findall(r'"([a-f0-9]{40,50})"', text)
                        if matches:
                            print(f"  ✅ Chunk '{chunk.split('/')[-1]}' has 'netshort':")
                            print(f"    Possible tokens: {matches[:3]}")
                        else:
                            print(f"  ℹ️  Chunk '{chunk.split('/')[-1]}' has 'netshort' (no hex tokens)")
            except: pass
    except Exception as e:
        print(f"  Error: {e}")


def test_episode_url(drama_id: str, slug: str, title: str, ep_num: int = 1):
    """Test getting video URL for a Netshort episode via RSC or API."""
    print(f"\n=== [4] Episode URL test: {title} Ep{ep_num} ===")

    # Method 1: Try direct Netshort API endpoint
    movie_url = f"{VIDRAMA_BASE}/movie/{slug}--{drama_id}?provider=netshort"
    watch_url  = f"{VIDRAMA_BASE}/watch/{slug}--{drama_id}/{ep_num}?provider=netshort"

    print(f"  Movie URL: {movie_url}")

    # Try RSC POST with auth (multiple possible next-action tokens)
    possible_actions = [
        # Known microdrama token (just for testing if it resolves)
        "40c1405810e1d492d36c686b19fdd772f47beba84f",
    ]

    for action_token in possible_actions:
        hdrs = {
            "next-action": action_token,
            "accept": "text/x-component",
            "content-type": "text/plain;charset=UTF-8",
            "origin": VIDRAMA_BASE,
            "referer": watch_url,
            "user-agent": "Mozilla/5.0",
            "Authorization": f"Bearer {ACCESS_TOKEN}",
        }
        try:
            r = requests.post(watch_url, headers=hdrs,
                              data=json.dumps([drama_id]).encode("utf-8"), timeout=20)
            print(f"  POST watch URL [{r.status_code}]: {r.text[:300]}")
            # Look for awscdn.netshort.com URLs in response
            mp4_urls = re.findall(r"https://awscdn\.netshort\.com/[^\s\"\\]+", r.text)
            if mp4_urls:
                print(f"  🎬 MP4 URLs found: {mp4_urls[:2]}")
        except Exception as e:
            print(f"  Error: {e}")

    # Method 2: Try direct Netshort API
    netshort_endpoints = [
        f"https://www.netshort.com/api/short/info?id={drama_id}&ep={ep_num}",
        f"https://api.netshort.com/v1/play?id={drama_id}&ep={ep_num}",
    ]
    for ep_url in netshort_endpoints:
        try:
            r = requests.get(ep_url, headers=get_auth_headers(), timeout=10)
            print(f"  [{r.status_code}] {ep_url}")
            if r.status_code == 200:
                print(f"    {r.text[:300]}")
        except Exception as e:
            print(f"  {ep_url}: {e}")


def main():
    print("=" * 60)
    print("  NETSHORT API PROBE v2 (JWT Auth)")
    print("=" * 60)

    # Try to refresh token first
    global ACCESS_TOKEN, REFRESH_TOKEN
    ACCESS_TOKEN, REFRESH_TOKEN = refresh_access_token()

    # Test Supabase REST API
    test_supabase_rest()

    # Test Vidrama API endpoints
    test_vidrama_api()

    # Find next-action token
    find_next_action_token()

    # Test episode URL for 2 dramas
    for drama in SAMPLE_DRAMAS[:2]:
        test_episode_url(drama["id"], drama["slug"], drama["title"], ep_num=1)
        time.sleep(1)

    # Save tokens for pipeline use
    config = {
        "access_token": ACCESS_TOKEN,
        "refresh_token": REFRESH_TOKEN,
        "supabase_url": SUPABASE_URL,
        "supabase_anon": SUPABASE_ANON,
    }
    Path("netshort_auth.json").write_text(json.dumps(config, indent=2))
    print("\n\n✅ Saved tokens: netshort_auth.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
