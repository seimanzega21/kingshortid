# -*- coding: utf-8 -*-
import requests
import json
import urllib3

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36',
    'Referer': 'https://vidrama.asia/watch/penyembuhnya-istrinya--ahTFgKtAU6/1?provider=dramawave&lang=id-ID',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; cf_clearance=J8QFuJs0er_WIP38vGy8bjQfQaQL7sFTKyEKgGeK3VA-1780795517-1.2.1.1-Obw73xI.dqmiSQdVtDuHFyZsbOD__sHZFc41Z7WuSJ_1XtPMHcVP7WGAmZM8UgRkfx1RmvPS8Mw6RV1Mxfy8nk9u5mLxnsCPd5XkJDAuQt5e1ZGXCvwfimrkbxXEBc0HLaV.tjy8GFC4chNPLXWwIu4XnAHluPvijjp6AziSEihvKlcO8S0gch2..hjZ.VvlLPFiQbKEWQd199XmWcHUjSlN1UbWgD9KtCXDZbIrrDBBDMAs874kQ6SiYfvaMVnn6MnmPE8TK1BVmFSj7tZDw.BioSjkB.O90BCUGYiLXLNnyCCnQCK4EiOE3hE7YmiOB08mCTr7Kh7ZZrGjyJQQaA; HstCnv5004644=64; HstCns5004644=86; panoramaId_expiry=1780881920064; HstCla5004644=1780795871370; HstPn5004644=2; HstPt5004644=159; ttcsid=1780795518124::qxBtmNAk35AwC3LWSvED.147.1780796502041.0::1.983569.353633::983547.23.360.812::604689.184.0; ttcsid_D5SNQPRC77UDQTF8A5EG=1780795518124::Zbl64-bTTugcPcmu7xs9.128.1780796502041.1; _ga_HCQQPKGEVH=GS2.1.s1780795517$o130$g1$t1780796502$j60$l0$h0'
}

url = "https://vidrama.asia/api/dramawave?action=list&page=1"
try:
    r = requests.get(url, headers=headers, verify=False)
    print("Status Code:", r.status_code)
    print("Response text:")
    print(r.text[:500])
except Exception as e:
    print("Error:", e)
