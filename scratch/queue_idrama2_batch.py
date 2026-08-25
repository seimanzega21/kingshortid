import subprocess
import time

ids = [
    "160000643080", # Sang CEO dan Tunangan Cleaning Service-nya
    "160000642812", # Profesor di Siang Hari, Tuanku di Malam Hari
    "160000643223"  # Ratu Dalam Diriku
]

for movie_id in ids:
    print(f"\n=======================================================")
    print(f"Starting IDRAMA2 scrape for movie_id: {movie_id}")
    print(f"=======================================================\n")
    
    cmd = ['python', 'scripts/scrape_idrama2_provider.py', movie_id]
    subprocess.run(cmd)
    
    print(f"\n[QUEUE] Sleeping for 15 seconds before next drama to prevent rate limiting...\n")
    time.sleep(15)

print("\nAll batch processing completed successfully!")
