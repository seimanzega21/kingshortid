import requests

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; global_ui_lang=id; cf_clearance=gi8rBDL4U_sV5dFUP.Dckjr.DONUzFar9fJlBMJx5_c-1778228148-1.2.1.1-rcSC4qbKF5H0KxB5Zt6Ic88iCIyXH7DESdcJA5w9WLWZvk58Y70clfcHFfqOyxmSRb1I97eRy.96PRr0zF1vV_PWs7vWkLZg2IsJNYLl5ZJvxdv7AnK4pZgxEBspgbrAod7jxce171vMiENcKPDXk_1eVFpBk_P5H8TA07xIBdq5HsL3uPTZKn8BCJv.HufjCR4mRr3DVOGDRagaNcc1CD_VmnRYY6tkanYH9QuDUyPeqreywRNxjb_5tsJVseZjz24po7Gw9o9ZVi3mSl9Ypm88Po1s4zr5n3DfE5R4BCKekPgqBAog2SDMQmDCWQJjMpzKKsJ_iXUHRaincYv9WQ; HstCnv5004644=43; HstCns5004644=47; panoramaId_expiry=1778314550106; HstCla5004644=1778228186632; HstPn5004644=2; HstPt5004644=85; _ga_HCQQPKGEVH=GS2.1.s1778254581$o93$g1$t1778255275$j47$l0$h0; ttcsid=1778254562634::VcwgkELj7wu61kAQZ9m6.110.1778255284779.0::1.721869.41379::721754.142.108.1170::721919.457.0; ttcsid_D5SNQPRC77UDQTF8A5EG=1778254578670::ru6ctqp2kzVRkgnn0scK.94.1778255284779.1'
}

def check_ep(ep):
    url = f"{VIDRAMA_API}/episode/1918527325729849346/{ep}?lang=id_ID"
    r = requests.get(url, headers=WEB_HDRS, verify=False)
    data = r.json()
    if data.get('code') == 200:
        videos = data['data'].get('videos', [])
        print(f"EP {ep} videos found:", len(videos))
        if videos:
            vurl = videos[0]['url']
            print("URL:", vurl[:100] + "...")
            r2 = requests.get(vurl, stream=True, headers=WEB_HDRS, verify=False)
            print("Status Code:", r2.status_code)
            length = r2.headers.get('Content-Length')
            print("Content-Length:", length)
    else:
        print(f"EP {ep} API error:", data)

print("Checking EP 3")
check_ep(3)
print("\nChecking EP 44")
check_ep(44)
