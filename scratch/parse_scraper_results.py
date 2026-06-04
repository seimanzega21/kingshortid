import re

log_path = r"C:\Users\Seiman\.gemini\antigravity\brain\62fd526c-6b76-4498-9b43-17b53236dbb6\.system_generated\tasks\task-190.log"

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

results = []
current_drama = ""

for line in lines:
    if "Processing drama:" in line:
        current_drama = line.strip()
    if "Scrape results for" in line:
        results.append(f"{current_drama} --> {line.strip()}")

print("=== Scraper Results Summary ===")
for r in results:
    print(r)
print(f"Total entries: {len(results)}")
