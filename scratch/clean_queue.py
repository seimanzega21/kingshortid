import re

with open('scratch/queue_reelshort_batch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Hapus yang kita tahu sudah didownload
content = re.sub(r'    "6a8ba7938db8c7372b0cf06e",.*\n', '', content)
content = re.sub(r'    "6a680dba16b0ffb8550360fc",.*\n', '', content)
content = re.sub(r'    "6a17a22b0d63ed7ca20b4781",.*\n', '', content)

with open('scratch/queue_reelshort_batch.py', 'w', encoding='utf-8') as f:
    f.write(content)
