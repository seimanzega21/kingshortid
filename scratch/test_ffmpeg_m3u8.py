import requests
import subprocess
import urllib3
import os
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCnv5004644=57; panorama_chat_expiry=180615916940; cf_clearance=VX_Xr7NRDn_bHR2_IRoxNdxL5BLxbzfsHkfsLSMFtA-1780530299-1.2.1.1-DhdR_gz24mRDxfqDZ6JRW4At_PbLTJ69TGIB31qouJlgG1ikLqNuWbm0okBLp1Go2MWem_3X.cMay4eQE7HLKx.Wz4KMiulNBq9fjyCxxmDPzi0YVkbw9OYiRi.jdLdpNnisuVfw8pLUT6D_YvEsubtvxlDh5jDYbq4oTMFkq1fE56yfDW6b6jn6IJ6bvb3akXHtVJ6OQFo1geg5Wb6Xw_ir7wl9U2yv1T0KvJKz4vMT0EgO6XLW1vbbwyS24o0gn_DLqysP7wxeeSoHslRpEeEXdsdPQjhy48S0JGs8NQPgxSoEuttjbRZEuqOiGjJjqCM6i9P9i1NArsF4tZuA; HstCns5004644=78; HstCla5004644=1780530357612; HstPn5004644=6; HstPt5004644=144; _ga_HCQQPKGEVH=GS2.1.s1780529507$o116$g1$t1780530797$j60$l0$h0; ttcsid=1780529507258::pJpTkBxKiHThj3O3zgcq.134.1780530904561.0::1.1288704.850729::1397297.32.106.1284::1396541.167.800; ttcsid_D5SNQPRC77UDQTF8A5EG=1780529507262::spplkSuwY5eRZp2hmJoH.116.1780530904561.1'
}

video_id = "MZJk8a"
ep_url = f"https://vidrama.asia/api/proxy-cubetv/episodes/{video_id}?lang=id"

print("Fetching episode details...")
r = requests.get(ep_url, headers=headers, verify=False, timeout=15)
if r.status_code == 200:
    data = r.json()
    eps = data if isinstance(data, list) else data.get('rows', data.get('data', []))
    first_ep = eps[0]
    m3u8_url = first_ep['videoUrls'][0]['url']
    print(f"M3U8 URL: {m3u8_url}")
    
    # Run FFmpeg to download/transcode
    out_file = "d:\\kingshortid\\scratch\\test_ffmpeg.mp4"
    if os.path.exists(out_file):
        os.remove(out_file)
        
    # We specify headers for FFmpeg
    headers_str = f"Referer: https://vidrama.asia/\r\nUser-Agent: {headers['User-Agent']}\r\n"
    
    cmd = [
        'ffmpeg', '-y',
        '-headers', headers_str,
        '-i', m3u8_url,
        '-c', 'copy', # Just copy streams for fast test
        out_file
    ]
    
    print("Running FFmpeg command...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"FFmpeg Return Code: {res.returncode}")
    if res.returncode == 0:
        print("Success! Output file created.")
        print(f"File size: {os.path.getsize(out_file)} bytes")
    else:
        print("Error:")
        print(res.stderr.decode('utf-8', errors='ignore'))
else:
    print(f"Error fetching episodes: {r.status_code}")
