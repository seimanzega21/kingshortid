import os
import re

js_dir = "d:\\kingshortid\\scratch\\js"
files = os.listdir(js_dir)

apis = set()
for filename in files:
    if not filename.endswith('.js'):
        continue
    filepath = os.path.join(js_dir, filename)
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    # Extract strings like "/api/..."
    matches = re.findall(r'"/api/[^"]*?"|\'/api/[^\']*?\'', content)
    for m in matches:
        apis.add(m)

print("=== Found API Paths in Client JS ===")
for api in sorted(apis):
    print(api)
