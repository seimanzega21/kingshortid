"""
mitmproxy addon: capture FreeReels auth_key from phone app traffic.
Save as: mitm_freereels.py

Run: mitmdump -p 8080 -s mitm_freereels.py
Then configure phone WiFi proxy → 192.168.1.7:8080
Open FreeReels app on phone → token auto-saved to fr_vip_token.json
"""
import json, logging
from pathlib import Path
from mitmproxy import http

TOKEN_FILE = Path(__file__).parent / 'fr_vip_token.json'
found = False

def response(flow: http.HTTPFlow):
    global found
    if found: return
    if 'apiv2.free-reels.com' not in flow.request.pretty_host: return

    try:
        text = flow.response.text
        data = json.loads(text)
        inner = data.get('data', {})
        ak    = inner.get('auth_key', '')
        ase   = inner.get('auth_secret', '')

        if ak and ase and len(ak) > 8:
            found = True
            token = {
                'auth_key':    ak,
                'auth_secret': ase,
                'user_id':     str(inner.get('user_id', '')),
                'nickname':    str(inner.get('nickname', inner.get('name', ''))),
                'url':         flow.request.url,
            }
            TOKEN_FILE.write_text(json.dumps(token, indent=2, ensure_ascii=False), encoding='utf-8')
            logging.warning('='*50)
            logging.warning('TOKEN BERHASIL DICAPTURE!')
            logging.warning(f'  auth_key:    {ak[:20]}...')
            logging.warning(f'  auth_secret: {ase[:20]}...')
            logging.warning(f'  user_id:     {inner.get("user_id")}')
            logging.warning(f'  nickname:    {inner.get("nickname","")}')
            logging.warning(f'  Saved → {TOKEN_FILE}')
            logging.warning('='*50)
            logging.warning('Bisa tutup proxy sekarang (Ctrl+C)')
    except:
        pass
