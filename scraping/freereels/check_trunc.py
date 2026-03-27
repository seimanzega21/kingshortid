"""Check truncation in parsed URLs"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('parsed_episodes.json') as f:
    data = json.load(f)

eps = data['episodes']
trunc_char = '\u2026'  # ellipsis character
truncated = [e for e in eps if trunc_char in e['h264']]
full = [e for e in eps if trunc_char not in e['h264']]

print(f'Total: {len(eps)}, Full URLs: {len(full)}, Truncated: {len(truncated)}')
for e in full[:3]:
    print(f"Ep {e['number']}: {e['h264'][:120]}")
for e in truncated[:3]:
    print(f"TRUNC Ep {e['number']}: {e['h264'][:120]}")
