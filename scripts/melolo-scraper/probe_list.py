import requests, json

url = "https://vidrama.asia/provider/netshortv2?_rsc=1p"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/x-component",
    "RSC": "1"
}

r = requests.get(url, headers=headers)
print("Fetch status:", r.status_code)

# Try parsing vidrama list
try:
    data = []
    # Find all shortPlayName or title patterns
    import re
    matches = re.findall(r'\"shortPlayId\":\"([0-9]+)\",.*?\"shortPlayName\":\"(.*?)\"', r.text)
    if matches:
        print(f"Found {len(matches)} dramas via shortPlayPattern")
        for m in matches[:10]:
            print(f" - {m[0]}: {m[1]}")
    else:
        print("No shortPlayPattern found. Trying another pattern...")
        matches2 = re.findall(r'\"id\":\"([A-Za-z0-9]+)\",\"title\":\"(.*?)\"', r.text)
        if matches2:
            print(f"Found {len(matches2)} dramas via id/title pattern")
            for m in matches2[:10]:
                print(f" - {m[0]}: {m[1]}")
        else:
            print("No dramas found. Dump summary:")
            print(r.text[:1000])

except Exception as e:
    print("Error:", e)

# Test Vidrama Netshort API directly?
print("\nTesting vidrama netshort API endpoint for list:")
try:
    r2 = requests.get("https://vidrama.asia/api/netshort?action=list", headers=headers)
    print("API list status:", r2.status_code)
    if r2.status_code == 200:
        d = r2.json()
        print("Keys:", d.keys() if isinstance(d, dict) else type(d))
        if isinstance(d, dict) and "data" in d:
            print(f"Contains {len(d['data'])} items in data")
except Exception as e:
    pass
