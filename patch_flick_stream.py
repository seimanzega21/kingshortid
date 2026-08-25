import re

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_code = """
        if not mp4_url:
            chapter_id = ep.get('chapter_id')
            if chapter_id:
                stream_url = f"https://vidrama.asia/api/proxy-flickreelsv2?action=stream&playletId={drama_id}&chapterId={chapter_id}&lang=id"
                try:
                    import cloudscraper
                    scraper = cloudscraper.create_scraper()
                    stream_r = scraper.get(stream_url, headers=headers, timeout=10)
                    mp4_url = stream_r.json().get('data', {}).get('hls_url', '')
                except:
                    pass

        if not mp4_url:"""

text = re.sub(r'\n\s+if not mp4_url:', new_code, text, count=1)

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Script updated successfully using regex.")
