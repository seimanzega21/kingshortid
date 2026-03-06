"""
FRESH SIGN GENERATOR - Get sign from app then make immediate API call
"""
import frida
import requests
import time
import json
import subprocess
from datetime import datetime

# Will be populated by Frida
fresh_sign = None
fresh_timestamp = None

def on_message(message, data):
    global fresh_sign, fresh_timestamp
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, dict):
            if payload.get('type') == 'sign':
                fresh_sign = payload.get('sign')
                fresh_timestamp = payload.get('timestamp')
                print(f"[OK] Got fresh sign: {fresh_sign[:50]}...")
        else:
            print(payload)

def get_fresh_sign(device, pid, path):
    """Get a fresh sign from the running app"""
    global fresh_sign, fresh_timestamp
    fresh_sign = None
    fresh_timestamp = None
    
    script_code = f"""
    Java.perform(function() {{
        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');
        
        var timestamp = Date.now().toString();
        var path = '{path}';
        
        send('[*] Generating fresh sign for: ' + path);
        
        var sign = AppUtils.getSign(timestamp, path);
        
        send({{type: 'sign', sign: sign, timestamp: timestamp, path: path}});
        send('[OK] Sign generated!');
    }});
    """
    
    session = device.attach(pid)
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    # Wait for sign
    for _ in range(10):
        if fresh_sign:
            break
        time.sleep(0.5)
    
    session.detach()
    return fresh_sign, fresh_timestamp

def make_api_call(path, body, sign, timestamp):
    """Make API call with fresh sign"""
    
    # Load base headers from captured file
    with open('captured-headers.json', 'r') as f:
        captured = json.load(f)
    
    headers = captured['headers'].copy()
    
    # Update with fresh sign and timestamp
    headers['sign'] = sign
    
    url = f"https://api-akm.goodreels.com/hwycclientreels{path}?timestamp={timestamp}"
    
    print(f"\n[API] Making API call:")
    print(f"    URL: {url}")
    print(f"    Sign: {sign[:50]}...")
    
    try:
        response = requests.post(url, json=body, headers=headers, timeout=15)
        print(f"    Status: {response.status_code}")
        
        result = response.json()
        if result.get('success'):
            print(f"    [SUCCESS]")
            return result
        else:
            print(f"    [FAILED] {result.get('message')}")
            return result
            
    except Exception as e:
        print(f"    [ERROR] {e}")
        return None

def main():
    print("=" * 60)
    print("FRESH SIGN API CALLER")
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
    
    # Test: Get home index
    print("\n" + "=" * 60)
    print("TEST: Home Index")
    print("=" * 60)
    
    sign, ts = get_fresh_sign(device, pid, '/home/index')
    
    if sign:
        result = make_api_call('/home/index', {
            'pageNo': 1,
            'pageSize': 12,
            'channelType': 3,
            'vipBookEnable': True,
            'channelId': -3
        }, sign, ts)
        
        if result and result.get('success'):
            data = result.get('data', {})
            books = data.get('bookList', [])
            print(f"\n>>> GOT {len(books)} BOOKS!")
            
            if books:
                print("\nFirst 3 books:")
                for book in books[:3]:
                    print(f"  - {book.get('bookName', 'Unknown')}")
    
    print("\n" + "=" * 60)
    print("DONE")

if __name__ == '__main__':
    main()

