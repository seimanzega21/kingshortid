with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("mp4_url = stream_r.json().get('data', {}).get('hls_url', '')", "mp4_url = stream_r.json().get('data', {}).get('hls_url', '')\n                    print(f\"      DEBUG STREAM API: {stream_r.status_code} - {stream_r.text[:50]}\")")

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'w', encoding='utf-8') as f:
    f.write(text)
