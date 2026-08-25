import re

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the drama list
text = re.sub(r'DRAMAS_TO_PROCESS = \[.*?\]', 
    "DRAMAS_TO_PROCESS = [{'id': '9515', 'slug': 'ratu-hamil-sang-bos-mafia', 'genres': ['Drama']}]", 
    text, flags=re.DOTALL)

# Replace fetch_drama_details and fetch_episode_url
new_funcs = """def fetch_drama_details(mid):
    import requests
    url = f'https://vidrama.asia/api/proxy-flickreelsv2?action=chapters&playletId={mid}&lang=id'
    headers = {
        'cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCmu5004644=1785595662344; HstCnv5004644=178; panoramaId_expiry=1787764330897; cf_clearance=zaFvp3AWfYI7g9uL7k4JJP45jHjosK5o5rUdeKa2f9w-1787678853-1.2.1.1-D2E5ctvydAf2d9TcI_TLgug_.vs2koHCfnz0w5j_cGqIaFY0ZgdpsbYxba8Azy2vA8qgUuFiK6H6w6Rgj8h3nzjEPlyGtJb6i3I1._Jxpo2pWTW.Yd_i.nflIb7cwJCkzYNLqVmlv._BsYGsf7MC7ZZJduusWeOp9a0zNXMD0FY3T_PspKw6GO0rZkh6GWUNigKuIWYA4TFJZa7j05HLo2YufhEbUr.bSE.yC9KnExPgqj5l2RMcpGuVM_giS90E7z5b0L_G1qoKA5abaAinwxXqzvg5e..RZtU0CYFSN_n.WUefRHuOCgS6.N8NaaTtd0AEUs8.2mzbHY3vOjFU.IrCGRI57ibDeKKSWaqqPS0; HstCns5004644=275; HstCla5004644=1787678868849; HstPn5004644=6; HstPt5004644=573; _ga_HCQQPKGEVH=GS2.1.s1787677858$o315$g1$t1787678986$j60$l0$h0; ttcsid=1787676822811::HgS6YSOTHkH34CVCO7K7.323.1787679124775.0::1.2157969.2046428::2301959.111.623.449::2191929.191.0; ttcsid_D5SNQPRC77UDQTF8A5EG=1787677857049::rZJGImbLODq_mmlEE2_0.289.1787679124775.1',
        'referer': 'https://vidrama.asia/'
    }
    r = requests.get(url, headers=headers, verify=False).json()
    metadata = r['data']
    metadata['chapterCount'] = len(metadata.get('list', []))
    metadata['shortPlayName'] = metadata['title']
    
    episodes = []
    for ep in metadata.get('list', []):
        episodes.append({
            'episodeNumber': ep['chapter_num'],
            'hls_url': ep.get('hls_url')
        })
    return metadata, episodes

def fetch_episode_url(mid, ep_no, episodes_data=None):
    if not episodes_data: return None
    for ep in episodes_data:
        if ep['episodeNumber'] == ep_no:
            url = ep.get('hls_url')
            if url:
                if 'proxy?url=' in url:
                    import urllib.parse
                    parsed = urllib.parse.urlparse(url)
                    query = urllib.parse.parse_qs(parsed.query)
                    url = query.get('url', [url])[0]
                return url
    return None"""

text = re.sub(r'def fetch_drama_details\(mid\):.*?def get_or_register_drama', new_funcs + '\n\ndef get_or_register_drama', text, flags=re.DOTALL)

# Also fix the call to fetch_episode_url to pass episodes_data!
text = text.replace('m3u8_url = fetch_episode_url(mid, ep_no)', 'm3u8_url = fetch_episode_url(mid, ep_no, episodes)')
text = text.replace('🚀 STARTING SHORTMAX QUEUE PIPELINE', '🚀 STARTING FLICKREELSV2 QUEUE PIPELINE')
text = text.replace('ALL SHORTMAX DRAMAS PROCESSED', 'ALL FLICKREELSV2 DRAMAS PROCESSED')

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'w', encoding='utf-8') as f:
    f.write(text)
