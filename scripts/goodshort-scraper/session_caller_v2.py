"""
COMPLETE SESSION CALLER v2 - With proper file logging
"""
import frida
import requests
import time
import json
import subprocess
import sys

# Configure output
LOG_FILE = 'api_result.log'

def log(msg):
    print(msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

# Clear log file
open(LOG_FILE, 'w').close()

session_data = {}

def on_message(message, data):
    global session_data
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, dict) and payload.get('type') == 'session':
            session_data = payload
            log(f"[OK] Session captured")
        elif isinstance(payload, str):
            log(payload)

def get_session_data(device, pid, path):
    global session_data
    session_data = {}
    
    script_code = f"""
    Java.perform(function() {{
        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');
        var SpData = Java.use('com.newreading.goodreels.utils.SpData');
        
        var timestamp = Date.now().toString();
        var path = '{path}';
        
        send('[*] Getting session...');
        
        var sign = AppUtils.getSign(timestamp, path);
        var userToken = SpData.getUserToken();
        var gaid = AppUtils.getGAID();
        var androidId = AppUtils.getAndroidID();
        
        send({{
            type: 'session',
            timestamp: timestamp,
            path: path,
            sign: sign,
            userToken: userToken,
            gaid: gaid,
            androidId: androidId
        }});
    }});
    """
    
    session = device.attach(pid)
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    for _ in range(15):
        if session_data:
            break
        time.sleep(0.5)
    
    session.detach()
    return session_data

def make_api_call(session, path, body):
    headers = {
        'sign': session['sign'],
        'Authorization': session['userToken'],
        'deviceId': session['gaid'],
        'androidId': session['androidId'],
        'pname': 'com.newreading.goodreels',
        'platform': 'ANDROID',
        'appVersion': '2782078',
        'Content-Type': 'application/json; charset=UTF-8',
        'User-Agent': 'okhttp/4.10.0',
        'scWidth': '1080',
        'scHeight': '2072',
        'language': 'en',
        'os': '11',
        'model': 'sdk_gphone_x86_64',
        'brand': 'google',
        'deviceType': 'phone',
    }
    
    url = f"https://api-akm.goodreels.com/hwycclientreels{path}?timestamp={session['timestamp']}"
    
    log(f"\n[API] URL: {url}")
    log(f"[API] Headers: {json.dumps(headers, indent=2)}")
    log(f"[API] Body: {json.dumps(body)}")
    
    try:
        response = requests.post(url, json=body, headers=headers, timeout=15)
        log(f"[API] Status: {response.status_code}")
        log(f"[API] Response: {response.text}")
        
        return response.json()
            
    except Exception as e:
        log(f"[ERROR] {e}")
        return None

def main():
    log("=" * 60)
    log("COMPLETE SESSION API CALLER v2")
    log("=" * 60)
    
    result = subprocess.run(['adb', 'shell', 'pidof', 'com.newreading.goodreels'],
                          capture_output=True, text=True)
    pid = int(result.stdout.strip()) if result.stdout.strip() else None
    
    if not pid:
        log("[!] App not running!")
        return
    
    log(f"[OK] App PID: {pid}")
    
    device = frida.get_usb_device()
    
    log("\nGetting session data...")
    session = get_session_data(device, pid, '/home/index')
    
    if not session:
        log("[!] Failed to get session")
        return
    
    log(f"\nSession timestamp: {session.get('timestamp')}")
    log(f"Session gaid: {session.get('gaid')}")
    log(f"Session androidId: {session.get('androidId')}")
    log(f"Session sign: {session.get('sign', '')[:80]}...")
    log(f"Session userToken: {session.get('userToken', '')[:80]}...")
    
    log("\nMaking API call...")
    result = make_api_call(session, '/home/index', {
        'pageNo': 1,
        'pageSize': 12,
        'channelType': 3,
        'vipBookEnable': True,
        'channelId': -3
    })
    
    log("\n" + "=" * 60)
    log("DONE - Check api_result.log for full output")

if __name__ == '__main__':
    main()
