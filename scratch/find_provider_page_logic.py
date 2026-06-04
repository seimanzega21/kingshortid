import os
import re

js_dir = "d:\\kingshortid\\scratch\\js"
files = os.listdir(js_dir)

print("=== Scanning JS files for provider page logic ===")
for filename in files:
    if not filename.endswith('.js'):
        continue
    filepath = os.path.join(js_dir, filename)
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    # Search for provider logic or API calls
    # Next.js calls for provider pages might have paths like '/provider/'
    if "/provider/" in content:
        print(f"\nFile {filename} has '/provider/'")
        # Let's print occurrences and some context
        for match in re.finditer(r'/provider/', content):
            start = max(0, match.start() - 150)
            end = min(len(content), match.end() + 150)
            print(f"  Context: {content[start:end]}")
            
    # Search for api calls containing movie/list or list or movies
    if "movie/list" in content or "movies/list" in content:
        print(f"\nFile {filename} has movie/list")
        for match in re.finditer(r'movie/list|movies/list', content):
            start = max(0, match.start() - 150)
            end = min(len(content), match.end() + 150)
            print(f"  Context: {content[start:end]}")
