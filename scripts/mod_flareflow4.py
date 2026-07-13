with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_stream = """              try:
                  stream_res = requests.get(stream_url, headers=WEB_HDRS, timeout=15, verify=False)
                  if stream_res.ok:
                      stream_data = stream_res.json().get('data', {})
                      vurl = stream_data.get('videoUrl')
                      subtitles = stream_data.get('subtitles', [])
              except Exception as e:"""

new_stream = """              try:
                  stream_res = requests.get(stream_url, headers=WEB_HDRS, timeout=15, verify=False)
                  if stream_res.ok:
                      stream_data = stream_res.json()
                      qualities = stream_data.get('qualities', {})
                      vurl = qualities.get('1080p') or qualities.get('720p') or qualities.get('480p') or stream_data.get('raw', {}).get('videoUrl') or stream_data.get('raw', {}).get('video_1080')
                      subtitles = stream_data.get('subtitles', [])
              except Exception as e:"""

code = code.replace(old_stream, new_stream)

with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'w', encoding='utf-8') as f:
    f.write(code)
