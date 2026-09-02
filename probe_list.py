import requests
import json
import re

hdrs = {'User-Agent': 'Mozilla/5.0'}

# Vidrama uses Next.js server actions. Maybe explore page uses it?
# Let's try to query the backend directly.
print("Trying /api/dotdrama?action=list or similar...")
r = requests.get('https://vidrama.asia/api/dotdrama?action=list', headers=hdrs)
if r.ok: print("action=list:", r.text[:200])

r2 = requests.get('https://vidrama.asia/api/dotdrama?action=home', headers=hdrs)
if r2.ok: print("action=home:", r2.text[:200])

r3 = requests.get('https://vidrama.asia/api/dotdrama?action=category', headers=hdrs)
if r3.ok: print("action=category:", r3.text[:200])

print("\nTrying to parse HTML of explore page...")
r_html = requests.get('https://vidrama.asia/id/explore', headers=hdrs)
print("HTML status:", r_html.status_code)
# Search for any json state
state_match = re.search(r'self\.__next_f\.push\(\[(.*?)\"data\":(.*?)]\)', r_html.text)
if state_match:
    print("Found next_f state!")

# Actually, if we look at Vidrama's Server Actions, they had an action for fetching lists.
# Instead of guessing, let's just use playwright to go to vidrama.asia/id/explore?provider=dotdrama and log all API requests.
