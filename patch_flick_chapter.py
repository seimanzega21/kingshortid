import re

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'\'hls_url\': ep\.get\(\'hls_url\'\)\s*\}', r"'hls_url': ep.get('hls_url'), 'chapter_id': ep.get('chapter_id')}", text)

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Regex replace applied.")
