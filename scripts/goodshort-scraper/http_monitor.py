"""
CAPTURE AT HTTP LAYER - Monitor semua network calls
"""
import frida
import json
import time
import subprocess
from datetime import datetime

captured = []

def on_message(message, data):
    global captured
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, dict):
            captured.append(payload)
            url = payload.get('url', '')[:60]
            print(f"[📡] {payload.get('type', 'unknown')}: {url}...")
        else:
            print(payload)

script_code = """
Java.perform(function() {
    send('[*] HTTP Layer Monitor');
    
    // Hook ALL URL connections
    try {
        var URL = Java.use('java.net.URL');
        URL.openConnection.overload().implementation = function() {
            var url = this.toString();
            if (url.includes('goodreels')) {
                send({type: 'URL', url: url, ts: Date.now()});
            }
            return this.openConnection();
        };
        send('[✓] URL.openConnection hooked');
    } catch(e) {
        send('[!] URL hook failed');
    }
    
    // Hook OkHttp Response to see actual traffic
    try {
        var Response = Java.use('okhttp3.Response');
        Response.body.implementation = function() {
            var request = this.request();
            var url = request.url().toString();
            
            if (url.includes('goodreels') && url.includes('/hwycclientreels/')) {
                send({type: 'RESPONSE', url: url, code: this.code()});
                
                // Try to get headers
                try {
                    var reqHeaders = request.headers();
                    var headers = {};
                    for (var i = 0; i < reqHeaders.size(); i++) {
                        headers[reqHeaders.name(i)] = reqHeaders.value(i);
                    }
                    send({type: 'HEADERS', url: url, headers: headers});
                } catch(e) {}
            }
            return this.body();
        };
        send('[✓] Response.body hooked');
    } catch(e) {
        send('[!] Response hook failed: ' + e.message);
    }
    
    // Also hook Retrofit calls if present
    try {
        var Retrofit = Java.use('retrofit2.Retrofit');
        send('[i] Retrofit class found');
    } catch(e) {}
    
    send('');
    send('[✅] Ready! Interact with the app...');
});
"""

def main():
    print("=" * 50)
    print("HTTP LAYER MONITOR")  
    print("=" * 50)
    
    result = subprocess.run(['adb', 'shell', 'pidof', 'com.newreading.goodreels'], 
                          capture_output=True, text=True)
    pid = int(result.stdout.strip()) if result.stdout.strip() else None
    
    if not pid:
        print("[!] App not running!")
        return
    
    print(f"[✓] PID: {pid}")
    
    device = frida.get_usb_device()
    session = device.attach(pid)
    
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    print("\n>>> INTERACT WITH APP NOW <<<\n")
    
    try:
        time.sleep(90)
    except KeyboardInterrupt:
        pass
    
    print(f"\n[💾] Captured {len(captured)} items")
    
    with open('http_capture.json', 'w') as f:
        json.dump(captured, f, indent=2)
    
    if captured:
        print("\nSample captures:")
        for item in captured[:5]:
            print(f"  {item.get('type')}: {item.get('url', '')[:50]}")

if __name__ == '__main__':
    main()
