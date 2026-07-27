import subprocess
import time

ids = [
    "6a583ce19cc2f14c4c0d4f50",
    "6a29062ef72802a0ca0b5d81",
    "66a1b0011b0a0dea9807b64b"
]

print(f"Starting batch process 2 for {len(ids)} Reelshort dramas...")

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
