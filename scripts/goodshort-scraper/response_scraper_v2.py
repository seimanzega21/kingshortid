"""
RESPONSE SCRAPER V2 - Hook at Buffer level
Try hooking okio.Buffer to catch all data being read
"""
import frida
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

captured = []

def on_message(message, data):
    global captured
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, dict):
            if payload.get('type') == 'response':
                url = payload.get('url', 'unknown')
                body = payload.get('body', '')[:500]
                print(f"\n[API] {url[:60]}...")
                print(f"      Body: {body[:100]}...")
                captured.append(payload)
            elif payload.get('type') == 'json_data':
                data_str = payload.get('data', '')[:200]
                print(f"[JSON] {data_str}")
                captured.append(payload)
        else:
            print(str(payload)[:100])

script_code = """
Java.perform(function() {
    send('[*] Response Scraper V2');
    
    // Try hooking Gson for JSON parsing
    try {
        var Gson = Java.use('com.google.gson.Gson');
        Gson.fromJson.overload('java.lang.String', 'java.lang.Class').implementation = function(json, clz) {
            var jsonStr = json ? json.toString() : '';
            if (jsonStr.includes('bookId') || jsonStr.includes('chapterId') || 
                jsonStr.includes('bookList') || jsonStr.includes('success')) {
                send({type: 'json_data', data: jsonStr.substring(0, 1000)});
            }
            return this.fromJson(json, clz);
        };
        send('[OK] Gson hooked');
    } catch(e) {
        send('[!] Gson hook failed');
    }
    
    // Hook JSONObject constructor
    try {
        var JSONObject = Java.use('org.json.JSONObject');
        JSONObject.$init.overload('java.lang.String').implementation = function(str) {
            var s = str ? str.toString() : '';
            if (s.includes('bookId') || s.includes('success":true')) {
                send({type: 'json_data', data: s.substring(0, 1000)});
            }
            return this.$init(str);
        };
        send('[OK] JSONObject hooked');
    } catch(e) {
        send('[!] JSONObject hook failed');
    }
    
    // Hook Call.execute for sync calls
    try {
        var Call = Java.use('okhttp3.Call');
        Call.execute.implementation = function() {
            var response = this.execute();
            try {
                var request = this.request();
                var url = request.url().toString();
                if (url.includes('goodreels')) {
                    send({type: 'call', url: url});
                }
            } catch(e) {}
            return response;
        };
        send('[OK] Call.execute hooked');
    } catch(e) {
        send('[!] Call.execute hook failed: ' + e.message);
    }
    
    // Hook RealCall.enqueue for async calls  
    try {
        var RealCall = Java.use('okhttp3.internal.connection.RealCall');
        RealCall.enqueue.implementation = function(callback) {
            var request = this.request();
            var url = request.url().toString();
            if (url.includes('goodreels')) {
                send({type: 'async_call', url: url.substring(0, 100)});
            }
            return this.enqueue(callback);
        };
        send('[OK] RealCall.enqueue hooked');
    } catch(e) {
        send('[!] RealCall hook failed: ' + e.message);
    }
    
    send('');
    send('[READY] Browse the app now!');
});
"""

def main():
    print("=" * 60)
    print("RESPONSE SCRAPER V2")
    print("=" * 60)
    
    result = subprocess.run(['adb', 'shell', 'pidof', 'com.newreading.goodreels'],
                          capture_output=True, text=True)
    pid = int(result.stdout.strip()) if result.stdout.strip() else None
    
    if not pid:
        print("[!] App not running!")
        return
    
    print(f"[OK] PID: {pid}")
    
    device = frida.get_usb_device()
    session = device.attach(pid)
    
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    print("\n>>> BROWSE APP NOW (2 minutes) <<<\n")
    
    try:
        time.sleep(120)
    except KeyboardInterrupt:
        pass
    
    session.detach()
    
    # Save
    output_dir = Path('scraped_data')
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / 'captured_v2.json', 'w', encoding='utf-8') as f:
        json.dump(captured, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Captured {len(captured)} items")

if __name__ == '__main__':
    main()
