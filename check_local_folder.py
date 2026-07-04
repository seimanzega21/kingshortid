# -*- coding: utf-8 -*-
import os

target_dir = r"D:\Video Drama\Facebook"
print(f"Checking if target directory exists: {target_dir}")
exists = os.path.exists(target_dir)
print(f"Exists: {exists}")
if exists:
    print("Contents of target directory:")
    try:
        print(os.listdir(target_dir))
    except Exception as e:
        print("Error listing dir:", e)
else:
    print("Target directory does not exist. Creating it...")
    try:
        os.makedirs(target_dir, exist_ok=True)
        print("Successfully created.")
    except Exception as e:
        print("Error creating dir:", e)
