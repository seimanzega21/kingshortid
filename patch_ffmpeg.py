import re

with open('ingest_netshort_local.py', 'r', encoding='utf-8') as f:
    s = f.read()

# Replace the 720p command
s = s.replace("'-c', 'copy',\n            '-movflags', '+faststart'",
              "'-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',\n            '-maxrate', '1500k', '-bufsize', '3000k', '-c:a', 'aac', '-b:a', '128k',\n            '-movflags', '+faststart'")

# Replace the 540p command
s = s.replace("'-vf', 'scale=-2:540',\n            '-c:v', 'libx264', '-crf', '26', '-preset', 'fast'",
              "'-vf', 'scale=540:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',\n            '-maxrate', '1000k', '-bufsize', '2000k', '-c:a', 'aac', '-b:a', '96k',\n            '-movflags', '+faststart'")

with open('ingest_netshort_local.py', 'w', encoding='utf-8') as f:
    f.write(s)
