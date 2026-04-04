#!/usr/bin/env python3
"""
Script to find drama "Dari Perjanjian ke Perasaan" and check/fix its 540p URLs.
This runs on the VPS via Coolify terminal.

Usage:
  1. Copy to VPS: scp find_and_fix_540p.py root@141.11.160.187:/tmp/
  2. Run: python3 /tmp/find_and_fix_540p.py

What it does:
  - Finds the drama and its episodes in the DB
  - Checks which episodes are missing videoUrl540p
  - Shows the existing videoUrl to determine the R2 path structure
  - Optionally provides the PATCH commands to fix it
"""

import subprocess
import json
import sys

DB_CONTAINER = "b9ea5fe215a0"
API_BASE = "https://api.shortlovers.id"

def psql(query):
    """Run a psql query and return the result."""
    cmd = [
        "docker", "exec", "-i", DB_CONTAINER,
        "psql", "-U", "postgres", "-t", "-c", query
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()

def main():
    print("=" * 60)
    print("Finding 'Dari Perjanjian ke Perasaan' drama...")
    print("=" * 60)

    # Find drama
    result = psql(
        "SELECT id, title, is_active FROM dramas WHERE title ILIKE '%perjanjian%perasaan%' OR title ILIKE '%dari perjanjian%' LIMIT 5;"
    )
    print("\n[DRAMA SEARCH RESULT]")
    print(result or "No drama found!")

    if not result:
        print("\nTrying broader search...")
        result = psql(
            "SELECT id, title, is_active FROM dramas WHERE title ILIKE '%perjanjian%' LIMIT 10;"
        )
        print(result or "Still nothing found!")
        return

    # Parse drama ID from first result
    lines = [l.strip() for l in result.split('\n') if l.strip() and '|' in l]
    if not lines:
        print("Could not parse drama ID")
        return

    drama_id = lines[0].split('|')[0].strip()
    drama_title = lines[0].split('|')[1].strip()
    print(f"\nFound drama: {drama_title} (ID: {drama_id})")

    # Check episodes 540p status
    print("\n[EPISODES 540P STATUS - First 10]")
    ep_result = psql(
        f"SELECT id, episode_number, "
        f"SUBSTRING(video_url, 1, 80) as video_url_preview, "
        f"CASE WHEN video_url_540p IS NOT NULL THEN '✓' ELSE '✗' END as has_540p "
        f"FROM episodes WHERE drama_id = '{drama_id}' "
        f"ORDER BY episode_number LIMIT 10;"
    )
    print(ep_result)

    # Count totals
    count_result = psql(
        f"SELECT COUNT(*) as total, "
        f"COUNT(video_url_540p) as with_540p, "
        f"COUNT(*) - COUNT(video_url_540p) as missing_540p "
        f"FROM episodes WHERE drama_id = '{drama_id}';"
    )
    print(f"\n[540P COVERAGE SUMMARY]")
    print(count_result)

    # Show the video URL structure
    print("\n[FIRST EPISODE VIDEO URL (to understand R2 path)]")
    url_result = psql(
        f"SELECT episode_number, video_url, video_url_540p "
        f"FROM episodes WHERE drama_id = '{drama_id}' "
        f"ORDER BY episode_number LIMIT 3;"
    )
    print(url_result)

    # Check if backfill script saw this drama
    print("\n[CHECKING IF DRAMA IS IN BACKFILL CHECKPOINT]")
    try:
        with open('/tmp/backfill_540p_checkpoint.json', 'r') as f:
            checkpoint = json.load(f)
            done = checkpoint.get('done', [])
            failed = checkpoint.get('fail', [])
            drama_in_done = any(drama_id in str(d) for d in done)
            drama_in_fail = any(drama_id in str(f) for f in failed)
            print(f"  In done list: {drama_in_done}")
            print(f"  In fail list: {drama_in_fail}")
            print(f"  Total done: {len(done)}, failed: {len(failed)}")
    except FileNotFoundError:
        print("  Checkpoint file not found (backfill may have finished or not running)")
    except Exception as e:
        print(f"  Error reading checkpoint: {e}")

if __name__ == '__main__':
    main()
