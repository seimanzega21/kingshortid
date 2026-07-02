from bs4 import BeautifulSoup
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("scratch/movie_page_QZpz60.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
scripts = soup.find_all("script")

print(f"Total scripts found: {len(scripts)}")
for i, s in enumerate(scripts):
    content = s.string if s.string else ""
    if "self.__next_f" in content:
        # Search for references to episodes or providers
        if "Bertani" in content or "Dewa" in content:
            print(f"Script {i} (len={len(content)}) contains drama title")
            # Let's write the content to a text file to read it
            with open(f"scratch/next_f_script_{i}.txt", "w", encoding="utf-8") as sf:
                sf.write(content)
            print(f"Saved script content to scratch/next_f_script_{i}.txt")
            
            # Look for episode IDs or details in this script
            # e.g., regex search for episode IDs which are usually 6 chars (alphanumeric like MZJk8a, ZMnoVa)
            ep_ids = re.findall(r'"episodeid":"([A-Za-z0-9]+)"', content)
            print("Found episode IDs:", ep_ids)
            
            # Let's print a snippet around "episode"
            idx = content.find("episode")
            if idx != -1:
                print("Snippet around 'episode':")
                print(content[max(0, idx-200):min(len(content), idx+500)])
