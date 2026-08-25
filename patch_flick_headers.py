import re

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

header_str = """
          mp4_url = ep.get('hls_url')
          if mp4_url and 'proxy?url=' in mp4_url:
              import urllib.parse
              mp4_url = urllib.parse.parse_qs(urllib.parse.urlparse(mp4_url).query).get('url', [mp4_url])[0]
          subs_list = []
          if not mp4_url:
              chapter_id = ep.get('chapter_id')
              if chapter_id:
                  stream_url = f"https://vidrama.asia/api/proxy-flickreelsv2?action=stream&playletId={drama_id}&chapterId={chapter_id}&lang=id"
                  try:
                      api_headers = {
                          'cookie': flickreelsv2_cookie,
                          'referer': 'https://vidrama.asia/'
                      }
                      stream_r = requests.get(stream_url, headers=api_headers, timeout=10, verify=False)
                      mp4_url = stream_r.json().get('data', {}).get('hls_url', '')
"""

text = re.sub(
    r'\n\s+mp4_url = ep\.get\(\'hls_url\'\).*?if chapter_id:\n\s+stream_url = .*?\n\s+try:\n\s+stream_r = requests\.get.*?timeout=10, verify=False\)\n\s+mp4_url = stream_r\.json\(\)\.get\(\'data\', \{\}\)\.get\(\'hls_url\', \'\'\)',
    header_str,
    text,
    flags=re.DOTALL
)

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Added api_headers to stream request")
