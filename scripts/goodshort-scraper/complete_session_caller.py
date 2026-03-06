"""
COMPLETE SESSION CALLER - Get ALL dynamic values from app then make API call
Sign, timestamp, userToken, deviceId, androidId - semua harus konsisten!
"""
import frida
import requests
import time
import json
import subprocess

# Captured session data
session_data = {}

def on_message(message, data):
    global session_data
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, dict) and payload.get('type') == 'session':
            session_data = payload
            print(f"[OK] Session captured!")
            print(f"    sign: {payload.get('sign', '')[:50]}...")
            print(f"    userToken: {payload.get('userToken', '')[:50]}...")
        else:
            print(str(payload)[:100])

def get_session_data(device, pid, path):
    """Get complete session data from app"""
    global session_data
    session_data = {}
    
    script_code = f"""
    Java.perform(function() {{
        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');
        var SpData = Java.use('com.newreading.goodreels.utils.SpData');
        
        var timestamp = Date.now().toString();
        var path = '{path}';
        
        send('[*] Getting complete session data...');
        
        // Get all values
        var sign = AppUtils.getSign(timestamp, path);
        var userToken = SpData.getUserToken();
        var gaid = AppUtils.getGAID();
        var androidId = AppUtils.getAndroidID();
        var userId = SpData.getUserId ? SpData.getUserId() : '';
        
        send({{
            type: 'session',
            timestamp: timestamp,
            path: path,
            sign: sign,
            userToken: userToken,
            gaid: gaid,
            androidId: androidId,
            userId: userId ? userId.toString() : ''
        }});
    }});
    """
    
    session = device.attach(pid)
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    # Wait for data
    for _ in range(15):
        if session_data:
            break
        time.sleep(0.5)
    
    session.detach()
    return session_data

def make_api_call(session, path, body):
    """Make API call with complete session data"""
    
    # Build headers from session - NOT from old capture
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
        # Static device info
        'scWidth': '1080',
        'scHeight': '2072',
        'language': 'en',
        'os': '11',
        'model': 'sdk_gphone_x86_64',
        'brand': 'google',
        'deviceType': 'phone',
    }
    
    if session.get('userId'):
        headers['userId'] = session['userId']
    
    url = f"https://api-akm.goodreels.com/hwycclientreels{path}?timestamp={session['timestamp']}"
    
    print(f"\n[API] Calling: {url[:70]}...")
    
    try:
        response = requests.post(url, json=body, headers=headers, timeout=15)
        print(f"    Status: {response.status_code}")
        
        result = response.json()
        if result.get('success'):
            print(f"    [SUCCESS!]")
            return result
        else:
            print(f"    [FAILED] {result.get('message')}")
            # Print response for debug
            print(f"    Response: {str(result)[:200]}")
            return result
            
    except Exception as e:
        print(f"    [ERROR] {e}")
        return None

def main():
    print("=" * 60)
    print("COMPLETE SESSION API CALLER")
    print("=" * 60)
    
    # Get app PID
    result = subprocess.run(['adb', 'shell', 'pidof', 'com.newreading.goodreels'],
                          capture_output=True, text=True)
    pid = int(result.stdout.strip()) if result.stdout.strip() else None
    
    if not pid:
        print("[!] App not running!")
        return
    
    print(f"[OK] App PID: {pid}")
    
    device = frida.get_usb_device()
    
    # Get session data
    print("\n" + "=" * 60)
    print("Getting session data from app...")
    print("=" * 60)
    
    session = get_session_data(device, pid, '/home/index')
    
    if not session:
        print("[!] Failed to get session data")
        return
    
    print("\nSession data captured:")
    for key in ['timestamp', 'gaid', 'androidId', 'userId']:
        if key in session:
            print(f"  {key}: {session[key]}")
    
    # Make API call
    print("\n" + "=" * 60)
    print("Making API call with fresh session...")
    print("=" * 60)
    
    result = make_api_call(session, '/home/index', {
        'pageNo': 1,
        'pageSize': 12,
        'channelType': 3,
        'vipBookEnable': True,
        'channelId': -3
    })
    
    if result and result.get('success'):
        data = result.get('data', {})
        books = data.get('bookList', [])
        print(f"\n>>> SUCCESS! Got {len(books)} books!")
        
        if books:
            print("\nFirst 3:")
            for book in books[:3]:
                print(f"  - {book.get('bookName', 'Unknown')}")
    
    print("\n" + "=" * 60)
    print("DONE")

if __name__ == '__main__':
    main()
