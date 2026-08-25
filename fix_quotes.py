with open('d:/kingshortid/ingest_shortmax_queue_vps.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("\\'", "'")
with open('d:/kingshortid/ingest_shortmax_queue_vps.py', 'w', encoding='utf-8') as f:
    f.write(text)
