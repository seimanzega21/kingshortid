import re

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

correct_block = """          mp4_url = ep.get('hls_url')
        if mp4_url and 'proxy?url=' in mp4_url:
            import urllib.parse
            mp4_url = urllib.parse.parse_qs(urllib.parse.urlparse(mp4_url).query).get('url', [mp4_url])[0]
        subs_list = []
        if not mp4_url:
            chapter_id = ep.get('chapter_id')
            if chapter_id:
                stream_url = f"https://vidrama.asia/api/proxy-flickreelsv2?action=stream&playletId={d['id']}&chapterId={chapter_id}&lang=id"
                try:
                    api_headers = {
                        'cookie': flickreelsv2_cookie,
                        'referer': 'https://vidrama.asia/'
                    }
                    stream_r = requests.get(stream_url, headers=api_headers, timeout=10, verify=False)
                    mp4_url = stream_r.json().get('data', {}).get('hls_url', '')
                except Exception as e:
                    print(f"      ⚠ Failed to fetch stream API: {e}")"""

# We need to find the block to replace. It starts at `mp4_url = ep.get('hls_url')` and ends at `Failed to fetch stream API: {e}")`
start_idx = text.find("          mp4_url = ep.get('hls_url')")
end_idx = text.find('Failed to fetch stream API: {e}")') + len('Failed to fetch stream API: {e}")')

if start_idx != -1 and text.find('Failed to fetch stream API') != -1:
    text = text[:start_idx] + correct_block + text[end_idx:]
    with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Block replaced successfully.")
else:
    print("Could not find block indices.")
