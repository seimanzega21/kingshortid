import re

with open('scratch/next_payload.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find any sequence of 10-20 digits
long_digits = re.findall(r'\b\d{10,22}\b', text)
print("Long digits found:", list(set(long_digits)))

# Also check for movie detail JSON structure
# e.g., "id":"...", "title":"..."
matches = re.findall(r'\"id\"\s*:\s*\"([^\"]+?)\"', text)
print("Found string IDs:", list(set(matches))[:10])

# Search for the idrama2 provider ID
# e.g., something like 161004641891
matches2 = re.findall(r'161004641891', text)
print("Occurrences of 161004641891:", len(matches2))
