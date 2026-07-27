import subprocess
import time

ids = [
    "699d1eefa3a7262cff05534b",
    "6a0d558d3c5868d64309bfdb",
    "69de1c45ea1c679364028a5b",
    "69b7b8dd5511dca44a0601ea",
    "6823f95c237444ee9a04f08a"
]

print(f"Starting batch process for {len(ids)} Reelshort dramas...")

for i, drama_id in enumerate(ids):
    print(f"\n==================================================")
    print(f"[{i+1}/{len(ids)}] Processing Drama ID: {drama_id}")
    print(f"==================================================")
    
    cmd = ["python", "scripts/scrape_reelshort_provider.py", drama_id]
    
    try:
        # Run sequentially
        subprocess.run(cmd, check=True)
        print(f"[{i+1}/{len(ids)}] SUCCESS - Finished {drama_id}")
    except subprocess.CalledProcessError as e:
        print(f"[{i+1}/{len(ids)}] ERROR - Failed to process {drama_id}. Exit code: {e.returncode}")
    
    print("Waiting 10 seconds before starting the next drama...")
    time.sleep(10)

print("\nAll batch tasks completed!")
