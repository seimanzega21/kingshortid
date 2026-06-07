# -*- coding: utf-8 -*-
from pathlib import Path
import tempfile
import os

temp_dir = Path(tempfile.gettempdir()) / 'dramawave_scraper'
print("Temp directory:", temp_dir)
if temp_dir.exists():
    files = list(temp_dir.glob("*"))
    print(f"Found {len(files)} files in temp dir:")
    for f in files:
        print(f"  {f.name} - Size: {f.stat().st_size} bytes")
else:
    print("Temp directory does not exist.")
