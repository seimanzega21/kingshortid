"""
FRIDA CAPTURE - ATTACH TO RUNNING APP
Gunakan ini SETELAH login, app sudah running
"""
import frida
import json
import time
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
                print(f"  [HEADER] {name}: {str(value)[:60]}...")
            elif payload.get('type') == 'request':
                captured_requests.append(payload)
                print(f"\n[📡] REQUEST captured!")
        else:
            print(payload)

script_code = """
Java.perform(function() {
    send('[*] Attaching to running GoodShort app...');
    
    // Hook getH5HeaderData - this is where ALL headers are prepared
    try {
        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');
        
        AppUtils.getH5HeaderData.implementation = function(timestamp, path) {
            send('[📋] API CALL: ' + path);
            send('    timestamp: ' + timestamp);
            
            var result = this.getH5HeaderData(timestamp, path);
            
            // Extract all headers from result Map
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
                send('[✓] Headers captured for: ' + path);
            } catch(e) {
                send('[!] Failed to extract: ' + e.message);
            }
            
            return result;
        };
        
        send('[✓] getH5HeaderData hooked');
    } catch(e) {
        send('[!] Hook failed: ' + e.message);
    }
    
    send('');
    send('[✅] Ready! Now scroll/tap in the app to trigger API calls...');
});
"""

def save_data():
    output = {
        'capturedAt': datetime.now().isoformat(),
        'headers': captured_headers,
        'requests': captured_requests
    }
    
    with open('captured_headers.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n[💾] Saved to captured_headers.json")

def main():
    print("=" * 60)
    print("ATTACH TO RUNNING GOODSHORT APP")
    print("=" * 60)
    print("\nMake sure:")
    print("  1. App is already running")
    print("  2. You are already logged in")
    print("  3. You can see the home screen")
    print("")
    
    device = frida.get_usb_device()
    
    # Get running process
    try:
        session = device.attach('com.newreading.goodreels')
        print("[✓] Attached to running app!")
    except Exception as e:
        print(f"[!] Could not attach: {e}")
        print("[?] Make sure the app is running first!")
        return
    
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    print("\n" + "=" * 60)
    print(">>> NOW SCROLL/TAP IN THE APP <<<")
    print(">>> This will trigger API calls <<<")
    print("=" * 60)
    print("\nListening for 120 seconds (Ctrl+C to stop early)...")
    
    try:
        time.sleep(120)
    except KeyboardInterrupt:
        print("\n[!] Stopped by user")
    
    save_data()
    
    print("\n" + "=" * 60)
    print("CAPTURED HEADERS:")
    for key in ['sign', 'timestamp', 'Authorization', 'deviceId', 'androidId', 'userId']:
        if key in captured_headers:
            print(f"  {key}: {str(captured_headers[key])[:80]}...")
    print("=" * 60)

if __name__ == '__main__':
    main()
