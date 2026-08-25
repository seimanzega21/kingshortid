with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace('except:\n                    pass', 'except Exception as e:\n                    print(f"      ⚠ Failed to fetch stream API: {e}")')
with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'w', encoding='utf-8') as f:
    f.write(text)
