import os
import re

js_dir = "d:\\kingshortid\\scratch\\js"
files = os.listdir(js_dir)

print("=== Scanning JS files ===")
for filename in files:
    if not filename.endswith('.js'):
        continue
    filepath = os.path.join(js_dir, filename)
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    # Search for endpoint constructions or strings with provider
    # E.g. /api/ or netshort or provider
    if "/api/" in content or "netshort" in content:
        # Find all strings like "/api/netshortv2/..."
        api_matches = re.findall(r'"/api/netshortv2/[^"]*?"|\'/api/netshortv2/[^\']*?\'', content)
        if api_matches:
            print(f"File {filename} has API endpoints: {list(set(api_matches))}")
            
        # Let's search for '/provider' or similar patterns
        prov_matches = re.findall(r'"/provider/[^"]*?"|\'/provider/[^\']*?\'', content)
        if prov_matches:
            print(f"File {filename} has provider routes: {list(set(prov_matches))}")
            
        # Search for any fetch calls that might be using provider dynamic values
        # like `provider=` or `?provider=`
        if "provider=" in content or "?provider=" in content or "&provider=" in content:
            print(f"File {filename} has 'provider=' query param reference!")
            # Get some context around 'provider='
            for match in re.finditer(r'provider=', content):
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                print(f"  Context: {content[start:end]}")
