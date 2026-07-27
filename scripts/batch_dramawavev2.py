import subprocess
import time

ids = [
    "SOYbpnZtWf",
    "hmo3r3U3Ft",
    "wlUr3JqHdQ",
    "v3YnooOBuD",
    "nwjt7o05OY"
]

print(f"Starting batch process for {len(ids)} Dramawavev2 dramas...")

for i, drama_id in enumerate(ids):
    print(f"\n==================================================")
    print(f"[{i+1}/{len(ids)}] Processing Drama ID: {drama_id}")
    print(f"==================================================")
    
    cmd = ["python", "scripts/scrape_dramawavev2_provider.py", drama_id]
    
    try:
        # Run sequentially
        subprocess.run(cmd, check=True)
        print(f"[{i+1}/{len(ids)}] SUCCESS - Finished {drama_id}")
    except subprocess.CalledProcessError as e:
        print(f"[{i+1}/{len(ids)}] ERROR - Failed to process {drama_id}. Exit code: {e.returncode}")
    
    print("Waiting 10 seconds before starting the next drama...")
    time.sleep(10)

print("\nAll Dramawavev2 batch tasks completed!")
