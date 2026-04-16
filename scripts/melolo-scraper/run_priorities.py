import subprocess
import time
import sys

def run_cmd(cmd):
    print(f"Running: {cmd}", flush=True)
    proc = subprocess.run(cmd, shell=True)
    if proc.returncode != 0:
        print(f"FAILED: {cmd}", flush=True)
    else:
        print(f"Finished: {cmd}", flush=True)
    time.sleep(2)

print("Executing Batch Scrape Pipeline....")

# 1. Satu Langkah Menjadi Dewa
run_cmd("python d:\\kingshortid\\scripts\\melolo-scraper\\scrape_netshort.py --scrape 2034157133506805762")

# 2. Legenda yang Terbuang
run_cmd("python d:\\kingshortid\\scripts\\melolo-scraper\\scrape_netshort.py --scrape 2041056545151647745")

# 3. Raja Tinju di Balik Gerobak
run_cmd("python d:\\kingshortid\\scripts\\melolo-scraper\\scrape_netshort.py --scrape 2037748734443388929")

# 5. Continue scraping other dramas
print("Starting daemon scraper to find other missing dramas...")
run_cmd("python d:\\kingshortid\\scripts\\melolo-scraper\\scrape_netshort.py --daemon --target 50")

print("All tasks completed!")
