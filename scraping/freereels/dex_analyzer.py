import os
import re

def extract_strings_from_binary(path, min_len=8, max_len=300):
    with open(path, 'rb') as f:
        data = f.read()
    pattern = rb'[\x20-\x7e]{' + str(min_len).encode() + rb',}'
    matches = re.findall(pattern, data)
    return [m.decode('ascii', errors='ignore') for m in matches]

dex = 'apk_decompile_raw/classes2.dex'
strings = extract_strings_from_binary(dex)

# Filter very specifically
api_strings = []
for s in strings:
    sl = s.lower()
    # URLs, secrets, keys, signing logic
    if any(x in sl for x in [
        'https://', 'http://', 'api.', '.com/v', 
        'mydramawave', 'freereels', 'dramareels',
        'hmac', 'sha256', 'sha1', 'secret', 
        'oauth', 'signature', 'getauth',
        'app-name', 'app-version', 'device-hash', 'device-id',
        'authorization', 'token',
        '/series/', '/book/', '/chapter/', '/user/',
        '/auth/', '/home/', '/channel/'
    ]):
        clean = s.strip()
        if clean and 8 < len(clean) < 250:
            api_strings.append(clean)

# Deduplicate
seen = set()
unique = []
for s in api_strings:
    if s not in seen:
        seen.add(s)
        unique.append(s)

print(f"Found {len(unique)} relevant strings in classes2.dex:")
print("=" * 60)
for s in sorted(unique):
    print(repr(s))
