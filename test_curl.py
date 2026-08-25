import requests

url = 'https://vidrama.asia/watch/dijulukisang-pembangkit-negara--843859/1?provider=shortmax&lang=id&_rsc=wxaqx'
headers = {
    'accept': '*/*',
    'accept-language': 'id,en-US;q=0.9,en;q=0.8,ms;q=0.7',
    'cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCmu5004644=1785595662344; cf_clearance=a_6iXAm1K87Jnho6xnrVrp8F9FVUchq_zdS6e9_wIbo-1787671087-1.2.1.1-9Fkzp6nP.wc4dshB06e1D18cQ22ea4PG6vpivpZffpVx1RqoyDjTYhOKzx9GKMDqje7eXDPu.4vFQfL7YgRncD36ujm9IkZidHOvSviuobbmT7ggT8b2NTpgA6yPioz_Bmh4mAL_xW_Y_3biosJ1D69kHY8Q_V6qMYFS4fCYb1hKB1VFvnEAphy6gTNZACnVv1jgGgRPHgmz.XfNiU9rLja4XR8Ahg06HMZtlk.vh6n1YNHmNkdfUlWcTHW7fG9ruJJwOrMSv0OYQWMktRGhCFZSqizCJy7u.LY7fYud3UjrTuJQRMixClkFQEhnyBxKPlMh6yOwgTIcorNkDX4hxvhdLEhfgA3deiFuzd2mC4A; HstCnv5004644=178; HstCns5004644=272; panoramaId_expiry=1787757513011; HstCla5004644=1787671440225; HstPn5004644=2; HstPt5004644=569; _ga_HCQQPKGEVH=GS2.1.s1787671080$o314$g1$t1787671923$j38$l0$h0; ttcsid=1787671081226::whj1kT8T0tmW-EizXFoo.322.1787672355335.0::1.841004.359377::1274103.42.621.529::819243.71.0; ttcsid_D5SNQPRC77UDQTF8A5EG=1787671081226::A0TVJ297C155kJHac0ru.288.1787672355335.1',
    'next-router-state-tree': '%5B%22%22%2C%7B%22children%22%3A%5B%22watch%22%2C%7B%22children%22%3A%5B%5B%22slug%22%2C%22dijulukisang-pembangkit-negara--843859%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%5B%22episode%22%2C%221%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%2Cfalse%5D%7D%2Cnull%2Cnull%2Cfalse%5D%7D%2Cnull%2Cnull%2Cfalse%5D%7D%2Cnull%2C%22refetch%22%2Cfalse%5D%7D%2Cnull%2Cnull%2Ctrue%5D',
    'next-url': '/movie/dijulukisang-pembangkit-negara--843859',
    'priority': 'u=1, i',
    'referer': 'https://vidrama.asia/movie/dijulukisang-pembangkit-negara--843859?provider=shortmax&lang=id',
    'rsc': '1',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36'
}

r = requests.post(url, headers=headers, data='[]')
import re
print("Searching for m3u8 in text of length:", len(r.text))
text_clean = r.text.replace('\\/', '/')
for m in re.findall(r'https?://[^\"]+?\.m3u8[^\"]*', text_clean):
    print("Found:", m)
