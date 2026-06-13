import re

with open("scratch/watch_payload.txt", "r", encoding="utf-8") as f:
    text = f.read()

chunks = re.findall(r'/_next/static/chunks/[^\s"\'\]]+', text)
print("Chunks in watch payload:")
for c in sorted(list(set(chunks))):
    print(c)
