# -*- coding: utf-8 -*-
import requests, json, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/en/watch/satu-pedang-tebas-raja-neraka--19820/1?provider=stardusttv',
    'Accept': 'text/x-component',
    'Content-Type': 'text/plain;charset=UTF-8',
}

def test_action(action_id, body_data):
    url = 'https://vidrama.asia/en/watch/satu-pedang-tebas-raja-neraka--19820/1?provider=stardusttv'
    hdrs = WEB_HDRS.copy()
    hdrs['next-action'] = action_id
    
    print(f"Calling Server Action {action_id} with body {body_data}...")
    r = requests.post(url, headers=hdrs, data=json.dumps(body_data), timeout=15, verify=False)
    print(f"Status: {r.status_code}")
    if r.ok:
        print(f"Response: {r.text[:500]}")
    else:
        print(f"Failed: {r.text[:300]}")

# Test metadata
test_action('60ea10e5421e7d8bbba1e0d453714768474e2a8880', ["19820", "id"])

# Test episode 1 stream
test_action('701fda472c36d458ba0a5efdba67386467d16aba38', ["19820", 1, "id"])

# Test episode 2 stream
test_action('701fda472c36d458ba0a5efdba67386467d16aba38', ["19820", 2, "id"])
