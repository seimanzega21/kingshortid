#!/usr/bin/env python3
"""
Chain launcher: waits for active parallel_scrape to finish, then starts 50 more.
Run this in a separate terminal.
"""
import subprocess, sys, time

print("=" * 60)
print("  CHAIN LAUNCHER: 50 dramas after current batch")
print("=" * 60)
print("\n  Starting 50-drama scrape now...")
print("  (Skips any dramas already in DB)\n")

# Just run parallel_scrape.py with --limit 50
# It auto-skips existing DB dramas, so no conflict with current batch
result = subprocess.run(
    [sys.executable, "parallel_scrape.py", "--limit", "50", "--workers", "4"],
    cwd=r"D:\kingshortid\scripts\melolo-scraper",
)

print(f"\nExit code: {result.returncode}")
