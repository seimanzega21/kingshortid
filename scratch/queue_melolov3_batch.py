import subprocess
import time
import sys

# Resuming sequentially starting from drama 7 (Dompet Ajaib Warisan Ibu)
dramas = [
    "7658950237255371781", # Dompet Ajaib Warisan Ibu
    "7655576632010214453", # Bodyguard Cantik Yang Nekat
    "7667782206168779829", # Kedai Kaki Lima Legendaris
    "7667109277349202949", # Ibu Gila Berubah Baik
    "7657812974429539333"  # Wanita Desa Ajaib
]

for idx, drama_id in enumerate(dramas, 1):
    print(f"\n[{idx}/{len(dramas)}] Starting melolov3 scraper for ID: {drama_id}")
    cmd = [sys.executable, "scripts/scrape_melolov3_provider.py", drama_id]
    try:
        subprocess.run(cmd, check=False)
    except Exception as e:
        print(f"Error running {drama_id}: {e}")
        
    print(f"Finished {drama_id}. Waiting 15 seconds before next drama to prevent CDN blocking...")
    time.sleep(15)
    
print("\nAll dramas in the resumed queue have been processed!")
