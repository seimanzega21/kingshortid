#!/usr/bin/env python3
"""Get full detail response for microdrama."""
import requests, sys, json
sys.stdout.reconfigure(encoding="utf-8")

DRAMA_ID = "2026484131354189825"
r = requests.get(f"https://vidrama.asia/api/microdrama?action=detail&id={DRAMA_ID}", timeout=15)
print(r.status_code)
if r.status_code == 200:
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))
