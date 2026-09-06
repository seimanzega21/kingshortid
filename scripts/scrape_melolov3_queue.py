#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort - melolov3 Queue Scraper
=================================
Membaca scripts/melolov3_queue.json dan memproses drama satu per satu secara berurutan.
"""
import sys
import json
import time
from pathlib import Path
import boto3
from botocore.config import Config

from scrape_melolov3_provider import scrape_single_drama, get_r2

QUEUE_PATH = Path(__file__).parent / 'melolov3_queue.json'

def load_queue():
    if not QUEUE_PATH.exists():
        return []
    try:
        with open(QUEUE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load queue: {e}")
        return []

def save_queue(queue):
    try:
        with open(QUEUE_PATH, 'w', encoding='utf-8') as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] Failed to save queue: {e}")

def run_queue():
    r2 = get_r2()
    print("=== KingShort melolov3 Queue Processor Started ===")

    while True:
        queue = load_queue()
        pending_items = [item for item in queue if item.get('status') in ['pending', 'processing']]

        if not pending_items:
            print("\n[INFO] All dramas in queue have been processed!")
            break

        current = pending_items[0]
        movie_id = current.get('id')
        title = current.get('title')

        print(f"\n=======================================================")
        print(f"[*] Processing: {title} (ID: {movie_id})")
        print(f"=======================================================")

        current['status'] = 'processing'
        save_queue(queue)

        try:
            success = scrape_single_drama(r2, movie_id, is_test_run=False)

            # Reload fresh queue to prevent overwriting manual edits
            queue = load_queue()
            for item in queue:
                if item.get('id') == movie_id:
                    item['status'] = 'done' if success else 'failed'
            save_queue(queue)

            if success:
                print(f"[SUCCESS] Finished drama: {title}")
            else:
                print(f"[FAILED] Finished with errors for drama: {title}")

        except KeyboardInterrupt:
            print("\n[INFO] Stopped by user.")
            break
        except Exception as e:
            print(f"[ERROR] Exception occurred while processing {title}: {e}")
            queue = load_queue()
            for item in queue:
                if item.get('id') == movie_id:
                    item['status'] = 'failed'
            save_queue(queue)

        time.sleep(3)

if __name__ == "__main__":
    run_queue()
