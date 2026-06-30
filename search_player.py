# -*- coding: utf-8 -*-
import requests, urllib3, sys, re
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

url = 'https://vidrama.asia/watch/satu-pedang-tebas-raja-neraka--19820/1?provider=stardusttv'
r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
if r.ok:
    # Find all iframes
    iframes = re.findall(r'<iframe[^>]*src="([^"]*)"[^>]*>', r.text)
    print(f"Iframes found: {iframes}")
    
    # Find player or video element
    players = re.findall(r'<div[^>]*id="player"[^>]*>|<video[^>]*>', r.text)
    print(f"Players/Videos found: {players}")
    
    # Print lines containing iframe or player or video
    for line in r.text.split('\n'):
        if any(w in line for w in ['iframe', 'player', 'video', 'src=']):
            if len(line.strip()) < 500:
                print(f"LINE: {line.strip()}")
else:
    print(f"Error {r.status_code}")
