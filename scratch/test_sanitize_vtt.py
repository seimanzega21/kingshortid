# -*- coding: utf-8 -*-
import requests
import re

url = "https://stream.shortlovers.id/dramawave/penyembuhnya-istrinya/ep001.vtt"
print("Downloading current VTT...")
r = requests.get(url, timeout=10)
if r.ok:
    content = r.text
    print("Original first 30 lines:")
    print("\n".join(content.split("\n")[:30]))
    
    # Sanitize
    sanitized = re.sub(r'font-size\s*:\s*\d+px\s*;?', '', content, flags=re.IGNORECASE)
    
    print("\nSanitized first 30 lines:")
    print("\n".join(sanitized.split("\n")[:30]))
    
    # Save sanitized file
    with open("d:/kingshortid/scratch/ep001_sanitized.vtt", "w", encoding="utf-8") as f:
        f.write(sanitized)
    print("\nSaved to d:/kingshortid/scratch/ep001_sanitized.vtt")
else:
    print("Failed to download:", r.status_code)
