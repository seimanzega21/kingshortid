#!/usr/bin/env python3
"""Test microdrama API endpoint variations."""
import requests, sys
sys.stdout.reconfigure(encoding="utf-8")

tests = [
    ("trending", "https://vidrama.asia/api/microdrama?action=trending&limit=5"),
    ("list lang=id", "https://vidrama.asia/api/microdrama?action=list&limit=5&language=id"),
    ("list lang=id2", "https://vidrama.asia/api/microdrama?action=list&limit=5&lang=id"),
    ("exclusive", "https://vidrama.asia/api/microdrama?action=exclusive&limit=5"),
    ("list category", "https://vidrama.asia/api/microdrama?action=list&limit=5&category=trending"),
    ("list country", "https://vidrama.asia/api/microdrama?action=list&limit=5&country=ID"),
    ("search cinta", "https://vidrama.asia/api/microdrama?action=search&keyword=cinta&limit=5"),
    ("search sang", "https://vidrama.asia/api/microdrama?action=search&keyword=sang&limit=5"),
    ("stream ep1", "https://vidrama.asia/api/microdrama?action=stream&id=2026484131354189825&episode=1"),
]

for name, url in tests:
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        dramas = data.get("dramas", data.get("data", []))
        if isinstance(dramas, list) and dramas:
            titles = [d.get("title","?") for d in dramas[:3]]
            print(f"[{r.status_code}] {name}: {len(dramas)} dramas -> {titles}")
        elif isinstance(data, dict):
            keys = list(data.keys())[:5]
            print(f"[{r.status_code}] {name}: keys={keys}, snippet={str(data)[:100]}")
        else:
            print(f"[{r.status_code}] {name}: empty/unexpected")
    except Exception as e:
        print(f"[ERR] {name}: {e}")
