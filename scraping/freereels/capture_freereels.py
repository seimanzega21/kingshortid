"""
mitmproxy addon script to capture FreeReels API traffic.
Run with: mitmdump -s capture_freereels.py -p 8888 --set block_global=false

Will save:
- HLS URLs (m3u8) → hls_urls.txt
- API requests → api_requests.txt
- Auth tokens → auth_token.txt
"""

import json
import os
import re
from datetime import datetime
from mitmproxy import http

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
HLS_FILE   = os.path.join(OUTPUT_DIR, "captured_hls.txt")
API_FILE   = os.path.join(OUTPUT_DIR, "captured_api.txt")
AUTH_FILE  = os.path.join(OUTPUT_DIR, "captured_auth.txt")

captured_hls   = set()
captured_auth  = set()

def _write(path, line):
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def request(flow: http.HTTPFlow):
    url = flow.request.pretty_url
    headers = dict(flow.request.headers)

    # Capture Authorization header
    auth = headers.get("authorization") or headers.get("Authorization")
    token = headers.get("token") or headers.get("Token")

    if auth and auth not in captured_auth:
        captured_auth.add(auth)
        line = f"[{datetime.now():%H:%M:%S}] Authorization: {auth}"
        print(f"🔑 {line}")
        _write(AUTH_FILE, line)
    if token and token not in captured_auth:
        captured_auth.add(token)
        line = f"[{datetime.now():%H:%M:%S}] Token: {token}"
        print(f"🔑 {line}")
        _write(AUTH_FILE, line)

    # Capture API calls
    if "mydramawave.com" in url or "freereels" in url.lower():
        req_body = ""
        try:
            req_body = flow.request.get_text()[:500]
        except:
            pass
        line = f"[{datetime.now():%H:%M:%S}] REQUEST: {flow.request.method} {url}"
        print(f"📡 {line}")
        _write(API_FILE, line)
        if req_body:
            _write(API_FILE, f"  BODY: {req_body}")
        for k, v in headers.items():
            if k.lower() in ["authorization", "token", "cookie", "x-api-key", "app-key"]:
                _write(API_FILE, f"  {k}: {v}")

def response(flow: http.HTTPFlow):
    url = flow.request.pretty_url
    content_type = flow.response.headers.get("content-type", "")

    # Capture HLS (m3u8) response
    if ".m3u8" in url or "m3u8" in url:
        if url not in captured_hls:
            captured_hls.add(url)
            line = f"[{datetime.now():%H:%M:%S}] HLS: {url}"
            print(f"🎬 {line}")
            _write(HLS_FILE, line)

    # Capture JSON response from API
    if "mydramawave.com" in url:
        try:
            body = flow.response.get_text()
            if len(body) < 20000:  # Save only small responses
                line = f"[{datetime.now():%H:%M:%S}] RESPONSE {url}"
                _write(API_FILE, line)
                _write(API_FILE, f"  {body[:2000]}")
                # Try to find HLS URLs in response
                hls_matches = re.findall(r'https://[^\s\'"]+\.m3u8[^\s\'"]*', body)
                for h in hls_matches:
                    if h not in captured_hls:
                        captured_hls.add(h)
                        hls_line = f"[{datetime.now():%H:%M:%S}] HLS-FROM-API: {h}"
                        print(f"🎬 {hls_line}")
                        _write(HLS_FILE, hls_line)
        except:
            pass
