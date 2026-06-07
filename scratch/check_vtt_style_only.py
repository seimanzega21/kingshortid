# -*- coding: utf-8 -*-
import requests

url = "https://stream.shortlovers.id/dramawave/penyembuhnya-istrinya/ep001.vtt"
r = requests.get(url, timeout=10)
lines = r.text.split("\n")
print("First 40 lines of VTT style block in R2:")
print("\n".join(lines[:40]))
