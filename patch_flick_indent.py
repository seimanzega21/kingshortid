with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
text = re.sub(r'          mp4_url = ep\.get\(\'hls_url\'\)', r"        mp4_url = ep.get('hls_url')", text)
text = re.sub(r'          if mp4_url and \'proxy\?url=\' in mp4_url:', r"        if mp4_url and 'proxy?url=' in mp4_url:", text)
text = re.sub(r'              import urllib\.parse', r"            import urllib.parse", text)
text = re.sub(r'              mp4_url = urllib\.parse\.parse_qs\(urllib\.parse\.urlparse\(mp4_url\)\.query\)\.get\(\'url\', \[mp4_url\]\)\[0\]', r"            mp4_url = urllib.parse.parse_qs(urllib.parse.urlparse(mp4_url).query).get('url', [mp4_url])[0]", text)
text = re.sub(r'          subs_list = \[\]', r"        subs_list = []", text)
text = re.sub(r'          if not mp4_url:', r"        if not mp4_url:", text)
text = re.sub(r'              chapter_id = ep\.get\(\'chapter_id\'\)', r"            chapter_id = ep.get('chapter_id')", text)
text = re.sub(r'              if chapter_id:', r"            if chapter_id:", text)
text = re.sub(r'                  stream_url = f"https://vidrama\.asia/api/proxy-flickreelsv2\?action=stream&playletId=\{drama_id\}&chapterId=\{chapter_id\}&lang=id"', r"                stream_url = f\"https://vidrama.asia/api/proxy-flickreelsv2?action=stream&playletId={drama_id}&chapterId={chapter_id}&lang=id\"", text)
text = re.sub(r'                  try:', r"                try:", text)
text = re.sub(r'                      api_headers = \{', r"                    api_headers = {", text)
text = re.sub(r'                          \'cookie\': flickreelsv2_cookie,', r"                        'cookie': flickreelsv2_cookie,", text)
text = re.sub(r'                          \'referer\': \'https://vidrama\.asia/\'', r"                        'referer': 'https://vidrama.asia/'", text)
text = re.sub(r'                      \}', r"                    }", text)
text = re.sub(r'                      stream_r = requests\.get\(stream_url, headers=api_headers, timeout=10, verify=False\)', r"                    stream_r = requests.get(stream_url, headers=api_headers, timeout=10, verify=False)", text)
text = re.sub(r'                      mp4_url = stream_r\.json\(\)\.get\(\'data\', \{\}\)\.get\(\'hls_url\', \'\'\)', r"                    mp4_url = stream_r.json().get('data', {}).get('hls_url', '')", text)
text = re.sub(r'                  except Exception as e:', r"                except Exception as e:", text)
text = re.sub(r'                      print\(f"      ⚠ Failed to fetch stream API: \{e\}"\)', r"                    print(f\"      ⚠ Failed to fetch stream API: {e}\")", text)


with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Indentation fixed.")
