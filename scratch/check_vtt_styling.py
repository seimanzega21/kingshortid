# -*- coding: utf-8 -*-
import requests

url = "https://stream.shortlovers.id/dramawave/penyembuhnya-istrinya/ep001.vtt"
r = requests.get(url, timeout=10)
lines = r.text.split("\n")
print(f"Total lines: {len(lines)}")
print("Sample cues (from line 100):")
print("\n".join(lines[100:150]))
