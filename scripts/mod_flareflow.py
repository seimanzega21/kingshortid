with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('dramawavev2', 'flareflow')
code = code.replace('DramaWaveV2', 'FlareFlow')
code = code.replace('f"https://vidrama.asia/api/flareflow?action=detail&id={movie_id}"', 'f"https://vidrama.asia/api/flareflow/detail?id={movie_id}&lang=id"')
code = code.replace('f"https://vidrama.asia/api/flareflow?action=stream&id={movie_id}&episode={ep_no}"', 'f"https://vidrama.asia/api/flareflow/episode?id={movie_id}&ep={ep_no}&lang=id"')

with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'w', encoding='utf-8') as f:
    f.write(code)
