import requests, re
url = 'https://vidrama.asia/watch/dijulukisang-pembangkit-negara--843859/1?provider=shortmax&lang=id'
headers = {
  'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
  'accept-language': 'id,en-US;q=0.9,en;q=0.8,ms;q=0.7',
  'cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCmu5004644=1785595662344; cf_clearance=a_6iXAm1K87Jnho6xnrVrp8F9FVUchq_zdS6e9_wIbo-1787671087-1.2.1.1-9Fkzp6nP.wc4dshB06e1D18cQ22ea4PG6vpivpZffpVx1RqoyDjTYhOKzx9GKMDqje7eXDPu.4vFQfL7YgRncD36ujm9IkZidHOvSviuobbmT7ggT8b2NTpgA6yPioz_Bmh4mAL_xW_Y_3biosJ1D69kHY8Q_V6qMYFS4fCYb1hKB1VFvnEAphy6gTNZACnVv1jgGgRPHgmz.XfNiU9rLja4XR8Ahg06HMZtlk.vh6n1YNHmNkdfUlWcTHW7fG9ruJJwOrMSv0OYQWMktRGhCFZSqizCJy7u.LY7fYud3UjrTuJQRMixClkFQEhnyBxKPlMh6yOwgTIcorNkDX4hxvhdLEhfgA3deiFuzd2mC4A; HstCnv5004644=178; HstCns5004644=272; panoramaId_expiry=1787757513011; HstCla5004644=1787671440225; HstPn5004644=2; HstPt5004644=569',
  'user-agent': 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36'
}
r = requests.get(url, headers=headers)
print("Status:", r.status_code)
urls = set(re.findall(r'https?://[^\"]+\.(?:jpg|jpeg|png|webp)', r.text))
print("URLS:")
for u in urls: print(u)
