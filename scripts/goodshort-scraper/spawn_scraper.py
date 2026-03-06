"""
SPAWN MODE SCRAPER - Force restart app and capture from startup
This ensures we catch the initial API calls before caching
"""
import frida
import json
import time
from datetime import datetime
from pathlib import Path

captured = []

def on_message(message, data):
    global captured
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, dict):
            if 'type' in payload:
                ptype = payload['type']
                if ptype in ['api_call', 'response', 'json_data']:
                    captured.append(payload)
                    print(f"[{ptype.upper()}] {str(payload)[:80]}...")
        else:
            print(str(payload)[:100])

script_code = """
setTimeout(function() {
    Java.perform(function() {
        send('[*] SPAWN MODE SCRAPER - App Starting Fresh');
        
        // Hook Retrofit for API calls (common in modern apps)
        try {
            // Hook HttpURLConnection
            var HttpURLConnection = Java.use('java.net.HttpURLConnection');
            HttpURLConnection.getInputStream.implementation = function() {
                var url = this.getURL().toString();
                if (url.includes('goodreels')) {
                    send({type: 'api_call', url: url, method: this.getRequestMethod()});
                }
                return this.getInputStream();
            };
            send('[OK] HttpURLConnection hooked');
        } catch(e) {}
        
        // Hook Gson
        try {
            var Gson = Java.use('com.google.gson.Gson');
            Gson.fromJson.overload('java.lang.String', 'java.lang.reflect.Type').implementation = function(json, type) {
                var jsonStr = json ? json.toString() : '';
                if (jsonStr.includes('"success"') || jsonStr.includes('bookId')) {
                    send({type: 'json_data', length: jsonStr.length, preview: jsonStr.substring(0, 500)});
                }
                return this.fromJson(json, type);
            };
            send('[OK] Gson Type overload hooked');
        } catch(e) {}
        
        try {
            var Gson = Java.use('com.google.gson.Gson');
            Gson.fromJson.overload('com.google.gson.JsonReader', 'java.lang.reflect.Type').implementation = function(reader, type) {
                send({type: 'json_reader', typeName: type.toString()});
                return this.fromJson(reader, type);
            };
            send('[OK] Gson JsonReader hooked');
        } catch(e) {}
        
        // Hook Response parsing at lower level
        try {
            var InputStreamReader = Java.use('java.io.InputStreamReader');
            InputStreamReader.$init.overload('java.io.InputStream').implementation = function(stream) {
                send({type: 'input_stream', info: 'InputStreamReader created'});
                return this.$init(stream);
            };
        } catch(e) {}
        
        // Hook async callback for OkHttp
        try {
            var Callback = Java.use('okhttp3.Callback');
            send('[i] OkHttp Callback class found');
        } catch(e) {}
        
        send('');
        send('[READY] Hooks active - waiting for API calls...');
    });
}, 3000); // Wait 3 seconds for app to initialize
"""

def main():
    print("=" * 60)
    print("SPAWN MODE SCRAPER")
    print("=" * 60)
    print("\nThis will RESTART the GoodShort app!")
    
    device = frida.get_usb_device()
    
    print("\n[1] Spawning app...")
    pid = device.spawn(['com.newreading.goodreels'])
    print(f"    PID: {pid}")
    
    print("[2] Attaching and loading script...")
    session = device.attach(pid)
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    print("[3] Resuming app...")
    device.resume(pid)
    
    print("\n" + "=" * 60)
    print(">>> APP STARTING - LOGIN AND BROWSE <<<")
    print(">>> Wait for hooks to be ready, then scroll <<<")
    print("=" * 60)
    print("\nCapturing for 3 minutes...")
    
    try:
        time.sleep(180)
    except KeyboardInterrupt:
        print("\n[!] Stopped")
    
    session.detach()
    
    # Save
    output_dir = Path('scraped_data')
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / 'spawn_capture.json', 'w', encoding='utf-8') as f:
        json.dump(captured, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Captured {len(captured)} items")
    print(f"[OK] Saved to scraped_data/spawn_capture.json")

if __name__ == '__main__':
    main()
