#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vidrama ReelShort Auto-Discovery
===============================
Searches Vidrama for candidate dramas, validates them as ReelShort provider,
and updates the local queue file `scripts/reelshort_queue.json`.
"""
import requests
import json
import urllib3
import time
import sys
import re
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding='utf-8')

API_BASE = 'https://api.shortlovers.id/api'
QUEUE_PATH = Path(__file__).parent / 'reelshort_queue.json'

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

KEYWORDS = ['dub', 'dubbing', 'versi dub', 'sulih suara', 'terjemahan', 'putri', 'suami', 'istri', 'cinta', 'bos', 'kaya']

def load_queue():
    if not QUEUE_PATH.exists():
        return []
    try:
        with open(QUEUE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Error reading queue file: {e}")
        return []

def save_queue(queue):
    try:
        with open(QUEUE_PATH, 'w', encoding='utf-8') as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
        print(f"Queue updated and saved. Total items: {len(queue)}")
    except Exception as e:
        print(f"[ERROR] Error saving queue file: {e}")

def check_duplicate_in_db(title):
    try:
        r = requests.get(f"{API_BASE}/dramas/search?q={title}", timeout=10)
        dramas = r.json().get('dramas', [])
        for d in dramas:
            if d['title'].lower().strip() == title.lower().strip():
                return True
    except Exception as e:
        print(f"[WARN] DB check duplicate error: {e}")
    return False

def clean_title(title):
    title = title.replace("(Sulih Suara)", "[Versi Dub]")
    title = title.replace("[Dubbing]", "[Versi Dub]")
    title = title.replace("[Dijuluki]", "[Versi Dub]")
    if "[Versi Dub]" not in title and any(kw in title.lower() for kw in ["dub", "dubbing", "sulih suara"]):
        title = f"[Versi Dub] {title}"
    return title.strip()

def discover_dramas():
    queue = load_queue()
    existing_ids = {item['id'] for item in queue}
    existing_titles = {item['title'].lower().strip() for item in queue}
    
    candidate_ids = set()
    
    print("=== Vidrama Global Search Crawling ===")
    for kw in KEYWORDS:
        url = f"https://vidrama.asia/api/search/global?q={kw}"
        print(f"Searching for '{kw}'...")
        try:
            r = requests.get(url, headers=WEB_HDRS, verify=False, timeout=20)
            if r.ok:
                data = r.json()
                items = data.get('data', [])
                for item in items:
                    vid_id = item.get('id')
                    if vid_id and vid_id not in existing_ids:
                        candidate_ids.add(vid_id)
            time.sleep(1)
        except Exception as e:
            print(f"  [ERROR] Searching '{kw}': {e}")
            
    # Filter only 24-character hexadecimal IDs (ReelShort format)
    candidate_ids = {str(vid_id) for vid_id in candidate_ids if re.match(r'^[0-9a-fA-F]{24}$', str(vid_id))}
    print(f"\nFound {len(candidate_ids)} candidate ReelShort IDs not present in the local queue.")
    
    new_entries = []
    
    for idx, vid_id in enumerate(sorted(candidate_ids), 1):
        print(f"[{idx}/{len(candidate_ids)}] Validating ID: {vid_id}... ", end="", flush=True)
        
        # Check ReelShort Detail API
        detail_url = f"https://vidrama.asia/api/reelshort/detail?id={vid_id}"
        try:
            r = requests.get(detail_url, headers=WEB_HDRS, verify=False, timeout=15)
            if r.ok:
                resp_json = r.json()
                if resp_json.get('success'):
                    detail = resp_json.get('detail', {})
                    raw_title = detail.get('title')
                    
                    if raw_title:
                        title = clean_title(raw_title)
                        
                        # Check local queue title duplicate
                        if title.lower().strip() in existing_titles:
                            print("SKIP (Local title duplicate)")
                            continue
                            
                        # Check db duplicate
                        if check_duplicate_in_db(title):
                            print("SKIP (Already exists in DB)")
                            continue
                            
                        entry = {
                            "id": vid_id,
                            "title": title,
                            "status": "pending",
                            "addedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "processedAt": None
                        }
                        new_entries.append(entry)
                        queue.append(entry)
                        existing_titles.add(title.lower().strip())
                        print(f"ADDED: {title}")
                        continue
            print("INVALID (Not a valid ReelShort drama or API failed)")
        except Exception as e:
            print(f"ERROR ({e})")
        
        # Rate limit friendly delay
        time.sleep(1)
        
    if new_entries:
        print(f"\nAdding {len(new_entries)} new dramas to the queue.")
        save_queue(queue)
    else:
        print("\nNo new dramas discovered.")

if __name__ == "__main__":
    discover_dramas()
