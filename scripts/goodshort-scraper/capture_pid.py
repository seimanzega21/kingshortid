"""
FRIDA CAPTURE - ATTACH VIA PID
"""
import frida
import json
import time
import subprocess
from datetime import datetime

captured_headers = {}
captured_requests = []

def on_message(message, data):
    global captured_headers, captured_requests
    if message['type'] == 'send':
        payload = message['payload']
        
        if isinstance(payload, dict):
            if payload.get('type') == 'header':
                name = payload.get('name')
                value = payload.get('value')
                captured_headers[name] = value
                print(f"  [H] {name}: {str(value)[:70]}...")
            elif payload.get('type') == 'request':
                captured_requests.append(payload)
                print(f"\n[📡] FULL REQUEST CAPTURED!")
        else:
            print(payload)

script_code = """
Java.perform(function() {
    send('[*] Attached! Hooking...');
    
    var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');
    
    AppUtils.getH5HeaderData.implementation = function(timestamp, path) {
        send('[📋] getH5HeaderData: ' + path);
        
        var result = this.getH5HeaderData(timestamp, path);
        
        try {
            var entrySet = result.entrySet();
            var iterator = entrySet.iterator();
            var headers = {};
            
            while (iterator.hasNext()) {
                var entry = iterator.next();
                var key = entry.getKey().toString();
                var value = entry.getValue().toString();
                headers[key] = value;
                send({type: 'header', name: key, value: value});
            }
            
            send({type: 'request', path: path, timestamp: timestamp, headers: headers});
        } catch(e) {
            send('[!] Error: ' + e.message);
        }
        
        return result;
    };
    
    send('[✓] Hook ready!');
    send('[i] Now scroll/tap in the app...');
});
"""

def get_pid():
    result = subprocess.run(['adb', 'shell', 'pidof', 'com.newreading.goodreels'], 
                          capture_output=True, text=True)
    pid = result.stdout.strip()
    return int(pid) if pid else None

def main():
    print("=" * 50)
    print("GOODSHORT CAPTURE - PID ATTACH")
    print("=" * 50)
    
    pid = get_pid()
    if not pid:
        print("[!] App not running!")
        return
    
    print(f"[✓] Found app with PID: {pid}")
    
    device = frida.get_usb_device()
    session = device.attach(pid)
    
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    print("\n>>> NOW SCROLL/TAP IN THE APP <<<\n")
    print("Listening for 90 seconds (Ctrl+C to stop)...")
    
    try:
        time.sleep(90)
    except KeyboardInterrupt:
        print("\n[!] Stopped")
    
    # Save
    with open('captured_headers.json', 'w') as f:
        json.dump({
            'capturedAt': datetime.now().isoformat(),
            'headers': captured_headers,
            'requests': captured_requests
        }, f, indent=2)
    
    print(f"\n[💾] Saved! Headers: {len(captured_headers)}, Requests: {len(captured_requests)}")
    
    if captured_headers:
        print("\n" + "=" * 50)
        print("KEY HEADERS:")
        for k in ['sign', 'timestamp', 'Authorization', 'deviceId', 'androidId', 'userId']:
            if k in captured_headers:
                print(f"  {k}: {captured_headers[k][:80]}...")

if __name__ == '__main__':
    main()
