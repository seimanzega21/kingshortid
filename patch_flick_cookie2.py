import re

new_cookie = "_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCmu5004644=1785595662344; HstCnv5004644=178; panoramaId_expiry=1787766188048; ttcsid_D5SNQPRC77UDQTF8A5EG=1787683282223::r5sn3E8CM-CMnygBKiK5.290.1787683510892.1; ttcsid=1787683281107::RPjamlVk9hI9IKuuDngb.324.1787683510892.0::1.229780.3154765::30801.118.208.1050::30878.203.0; _ga_HCQQPKGEVH=GS2.1.s1787683283$o316$g1$t1787683511$j60$l0$h0; cf_clearance=ZhUAogRxdJLR.DbUFXFH3Skv5XhM95AQzLphe8f8E5M-1787683519-1.2.1.1-mW1GH4dDs6QTKaUdx4_Du.o7Bgh.VNLszuj.nb8Z5xOw.YK6x.mRRguJQoTWRpPX43n7uNl5.jmUiuhhPpnCblzw55R4iey9B.RAK2z3YfmOCuXmg_KJivgkejaKR4nTtAMVHgHqOGnYdNnfMCJNqDJUBmSLBv9MLE9S2Uh3Ke2_IWkTuP5y2xYVSsycoZ5AeIUiA5BQ8pcLUnjvLV2tA7rHjflA3.J2OSGhXPeQP4g4P_pPUvrJEjn.Dy3YW_zUytFICOBn_uP9wNEtQgUQSZJhrPSLlAtBGnNyupt53KGEEkQGExwfPbbfMK8GkELf51Rmiiw3BDhZ2KE504pfqRjKftn3TTcfvLOF5bkuyKw; HstCla5004644=1787683512634; HstPn5004644=9; HstPt5004644=576; HstCns5004644=277"

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'\'cookie\':\s*(["\']).*?\1', f"'cookie': '{new_cookie}'", text)

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Cookie patched successfully.")
