import re
import os
import sys

# Force output to utf-8 in case we run in terminal
sys.stdout.reconfigure(encoding='utf-8')

js_files = [
    "8b621ebc316f20de.js",
    "4ba947795445f824.js",
    "111e904f7cf906e0.js",
    "c13d18b2b15b9a28.js",
    "a44235986dc198f3.js",
    "75b5c11343842a8d.js",
    "593c89760da5ad12.js",
    "d6e427dd11a55e6a.js",
    "54100d0d389c63ef.js",
    "fa58348e1cfbeff8.js",
    "3b20f704ccd51e92.js",
    "85645474589c9371.js",
    "337a0aff989a89d1.js",
    "768b73b63e9105b4.js",
    "474b20d915704880.js",
    "c210b9c481d1d663.js",
    "a6dad97d9634a72d.js",
    "7c862900ddac2100.js"
]

results = []

results.append("=== Searching for API patterns ===")
for filename in js_files:
    local_path = f"d:\\kingshortid\\scratch\\js\\{filename}"
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Look for search/feed/movies/provider occurrences
        if "provider" in content or "feed" in content or "netshort" in content:
            results.append(f"\nFile {filename} contains target keywords")
            
            # Let's search for API URL constructions
            matches = re.findall(r'"[^"]*?api/netshortv2[^"]*?"|\'[^\']*?api/netshortv2[^\']*?\'', content)
            if matches:
                results.append(f"  Found netshortv2 endpoint strings: {matches}")
                
            # Search for provider-related routes
            prov_matches = re.findall(r'"[^"]*?provider[^"]*?"|\'[^\']*?provider[^\']*?\'', content)
            # Filter matches to look like paths or API queries
            filtered_prov = [m for m in prov_matches if '/' in m or '=' in m or 'api' in m]
            if filtered_prov:
                results.append(f"  Found provider endpoint/path strings (sample): {filtered_prov[:10]}")

with open("d:\\kingshortid\\scratch\\js_search_results.txt", "w", encoding="utf-8") as f_out:
    f_out.write("\n".join(results))

print("Scan completed. Results written to scratch\\js_search_results.txt")
