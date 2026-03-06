#!/usr/bin/env python3
"""Check microdrama detail + stream API structure for an Indonesian drama."""
import requests, sys, json
sys.stdout.reconfigure(encoding="utf-8")

# Test with a drama from the list
DRAMA_ID = "2026484131354189825"  # First drama

# Detail
r = requests.get(f"https://vidrama.asia/api/microdrama?action=detail&id={DRAMA_ID}", timeout=15)
print(f"Detail status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    print(json.dumps(d, ensure_ascii=False, indent=2)[:1500])
print()

# Stream
r2 = requests.get(f"https://vidrama.asia/api/microdrama?action=stream&id={DRAMA_ID}&episode=1", timeout=15)
print(f"Stream status: {r2.status_code}")
if r2.status_code == 200:
    print(json.dumps(r2.json(), ensure_ascii=False, indent=2)[:1000])
else:
    print(r2.text[:400])
print()

# Try Indonesian search via melolo
r3 = requests.get("https://vidrama.asia/api/microdrama?action=search&keyword=cinta&limit=5&lang=id", timeout=15)
print(f"Search cinta: {r3.status_code}")
print(r3.text[:400])
