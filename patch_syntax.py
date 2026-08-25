with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(r'f\"https://vidrama.asia/api/proxy-flickreelsv2?action=stream&playletId={drama_id}&chapterId={chapter_id}&lang=id\"', r'f"https://vidrama.asia/api/proxy-flickreelsv2?action=stream&playletId={drama_id}&chapterId={chapter_id}&lang=id"')

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'w', encoding='utf-8') as f:
    f.write(text)
