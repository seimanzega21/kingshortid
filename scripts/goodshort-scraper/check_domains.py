import json
from pathlib import Path
from collections import Counter

har_file = Path("har_files/batch_01.har")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data['log']['entries']

# Extract all domains
domains = []
for entry in entries:
    url = entry['request']['url']
    try:
        domain = url.split('/')[2]
        domains.append(domain)
    except:
        pass

# Count
domain_counts = Counter(domains)

print(f"Total requests: {len(entries)}\n")
print("Top 20 domains:")
for domain, count in domain_counts.most_common(20):
    print(f"  {count:4d}  {domain}")
