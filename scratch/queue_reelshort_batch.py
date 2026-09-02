import subprocess
import time

ids = [
    "6a680dba16b0ffb8550360fc", # Zero to Alpha: Kembalinya Raja Serigala
    "6a8ba7938db8c7372b0cf06e", # Terlahir Kembali Membangun Kekaisaran
]

for movie_id in ids:
    print(f"\n=======================================================")
    print(f"Starting REELSHORT scrape for movie_id: {movie_id}")
    print(f"=======================================================\n")
    
    cmd = ['python', 'scripts/scrape_reelshort_provider.py', movie_id]
    subprocess.run(cmd)
    
    print(f"\n[QUEUE] Sleeping for 15 seconds before next drama to prevent rate limiting...\n")
    time.sleep(15)

print("\nAll batch processing completed successfully!")
