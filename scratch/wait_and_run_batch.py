# -*- coding: utf-8 -*-
import time
import os
import subprocess
import sys

log_file_path = r"C:\Users\Seiman\.gemini\antigravity\brain\15222c7d-6854-46c7-8b06-40fef6eda44f\.system_generated\tasks\task-1759.log"
batch_script = r"d:\kingshortid\scripts\batch_scrape_dramawave.py"

print("Starting monitor for scrape_dramawave_provider.py (task-1759)...")
print(f"Monitoring log: {log_file_path}")

completed = False
checks = 0

while True:
    checks += 1
    # Check if the log file exists and contains the completion summary
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "Scrape results for" in content:
                    print("Detected completion line in log file! Scraper task-1759 is finished.")
                    completed = True
                    break
        except Exception as e:
            print(f"Error reading log file: {e}")
            
    # As a fallback, check if wmic can find the python command for scrape_dramawave_provider
    try:
        # Check if the python process for scrape_dramawave_provider is running
        cmd = 'wmic process where "CommandLine like \'%scrape_dramawave_provider%\'" get ProcessId'
        output = subprocess.check_output(cmd, shell=True, text=True)
        lines = [line.strip() for line in output.split('\n') if line.strip()]
        # If wmic only returned headers (ProcessId) and no PIDs
        if len(lines) <= 1:
            print("No active scrape_dramawave_provider process found via wmic.")
            completed = True
            break
    except Exception as e:
        pass
        
    print(f"Check #{checks}: Task is still running. Waiting 30 seconds...")
    time.sleep(30)

if completed:
    print("\nLaunching batch scraper sequentially...")
    sys.stdout.flush()
    
    # Run the batch scraper
    cmd_run = [sys.executable, batch_script]
    try:
        # We run it and let its stdout/stderr go to parent stdout/stderr
        subprocess.run(cmd_run, check=True)
        print("Batch scraper completed successfully!")
    except Exception as e:
        print(f"Error running batch scraper: {e}")
else:
    print("Monitor ended without launching batch scraper.")
