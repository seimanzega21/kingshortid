# -*- coding: utf-8 -*-
import os

base_dir = r"D:\Video Drama\Facebook"
for folder in os.listdir(base_dir):
    target = os.path.join(base_dir, folder)
    if os.path.isdir(target):
        print(f"\nContents of folder '{folder}':")
        files = [f for f in os.listdir(target) if os.path.isfile(os.path.join(target, f))]
        for f in files[:10]:
            print(f"  {f}")
