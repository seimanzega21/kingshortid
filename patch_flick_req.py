import re

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_code = """
        if not mp4_url:
            chapter_id = ep.get('chapter_id')
            if chapter_id:
                stream_url = f"https://vidrama.asia/api/proxy-flickreelsv2?action=stream&playletId={drama_id}&chapterId={chapter_id}&lang=id"
                try:
                    stream_r = requests.get(stream_url, headers=headers, timeout=10, verify=False)
                    mp4_url = stream_r.json().get('data', {}).get('hls_url', '')
                except Exception as e:
                    print(f"      ⚠ Failed to fetch stream API: {e}")
"""

text = re.sub(r'\n\s+if not mp4_url:\n\s+chapter_id = ep\.get\(\'chapter_id\'\).*?except Exception as e:\n\s+print\(f"      ⚠ Failed to fetch stream API: \{e\}"\)', new_code, text, flags=re.DOTALL)

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Script updated successfully to use requests instead of cloudscraper for stream API.")
