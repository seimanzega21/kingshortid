"""
FRIDA CAPTURE v2 - Hook at multiple levels to catch ALL requests
"""
import frida
import json
import time
import os
from datetime import datetime

captured_requests = []
captured_headers = {}

def on_message(message, data):
    global captured_requests, captured_headers
    if message['type'] == 'send':
        payload = message['payload']
        
        if isinstance(payload, dict):
            if payload.get('type') == 'header':
                name = payload.get('name')
                value = payload.get('value')
                captured_headers[name] = value
                if name in ['sign', 'timestamp', 'Authorization']:
                    print(f"  [HEADER] {name}: {str(value)[:60]}...")
            elif payload.get('type') == 'request':
                captured_requests.append(payload)
                print(f"\n[📡] REQUEST: {payload.get('url', '')[:80]}")
        else:
            print(payload)
    elif message['type'] == 'error':
        print(f"[ERROR] {str(message)[:200]}")

script_code = """
Java.perform(function() {
    send('[*] GoodShort Capture v2');
    
    // Method 1: Hook HttpURLConnection
    try {
        var HttpURLConnection = Java.use('java.net.HttpURLConnection');
        
        HttpURLConnection.setRequestProperty.implementation = function(key, value) {
            var url = '';
            try { url = this.getURL().toString(); } catch(e) {}
            
            if (url.includes('goodreels')) {
                send({type: 'header', name: key, value: value, url: url});
            }
            return this.setRequestProperty(key, value);
        };
        
        send('[✓] HttpURLConnection.setRequestProperty hooked');
    } catch(e) {
        send('[!] HttpURLConnection hook failed');
    }
    
    // Method 2: Hook at URL level
    try {
        var URL = Java.use('java.net.URL');
        URL.openConnection.overload().implementation = function() {
            var url = this.toString();
            if (url.includes('goodreels.com') && url.includes('/hwycclientreels/')) {
                send({type: 'request', url: url, timestamp: Date.now()});
            }
            return this.openConnection();
        };
        send('[✓] URL.openConnection hooked');
    } catch(e) {
        send('[!] URL.openConnection hook failed');
    }
    
    // Method 3: Hook OkHttp at the lowest level
    try {
        var OkHttpClient = Java.use('okhttp3.OkHttpClient');
        OkHttpClient.newCall.implementation = function(request) {
            var url = request.url().toString();
            
            if (url.includes('goodreels.com') && url.includes('/hwycclientreels/')) {
                send('[🎯] OkHttp call: ' + url);
                
                var headers = request.headers();
                var headerMap = {};
                
                // Try to get all headers
                try {
                    for (var i = 0; i < headers.size(); i++) {
                        var name = headers.name(i);
                        var value = headers.value(i);
                        headerMap[name] = value;
                        send({type: 'header', name: name, value: value, url: url});
                    }
                } catch(e) {
                    send('[!] Failed to iterate headers: ' + e.message);
                }
                
                send({type: 'request', url: url, method: request.method(), headers: headerMap, timestamp: Date.now()});
            }
            
            return this.newCall(request);
        };
        send('[✓] OkHttpClient.newCall hooked');
    } catch(e) {
        send('[!] OkHttpClient.newCall hook failed: ' + e.message);
    }
    
    // Method 4: Hook getH5HeaderData to see headers being prepared
    try {
        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');
        
        AppUtils.getH5HeaderData.implementation = function(timestamp, path) {
            send('[📋] getH5HeaderData called: path=' + path + ', ts=' + timestamp);
            
            var result = this.getH5HeaderData(timestamp, path);
            
            // Result is a Map, try to extract
            try {
                var Set = Java.use('java.util.Set');
                var entrySet = result.entrySet();
                var iterator = entrySet.iterator();
                
                var headers = {};
                while (iterator.hasNext()) {
                    var entry = iterator.next();
                    var key = entry.getKey().toString();
                    var value = entry.getValue().toString();
                    headers[key] = value;
                    
                    if (key === 'sign' || key === 'timestamp' || key === 'Authorization') {
                        send({type: 'header', name: key, value: value, source: 'getH5HeaderData'});
                    }
                }
                
                send({type: 'request', url: path, headers: headers, timestamp: timestamp, source: 'getH5HeaderData'});
            } catch(e) {
                send('[!] Failed to extract headers from map: ' + e.message);
            }
            
            return result;
        };
        send('[✓] AppUtils.getH5HeaderData hooked');
    } catch(e) {
        send('[!] AppUtils.getH5HeaderData hook failed: ' + e.message);
    }
    
    send('');
    send('[✅] All hooks ready! Browse the app now...');
});
"""

def save_data():
    global captured_requests, captured_headers
    
    output = {
        'capturedAt': datetime.now().isoformat(),
        'headers': captured_headers,
        'requests': captured_requests
    }
    
    with open('captured_full.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n[💾] Saved to captured_full.json")
    print(f"    Headers: {len(captured_headers)}")
    print(f"    Requests: {len(captured_requests)}")

def main():
    print("=" * 60)
    print("GOODSHORT CAPTURE v2")
    print("=" * 60)
    
    device = frida.get_usb_device()
    
    print("\n[1] Clearing app data...")
    os.system('adb shell pm clear com.newreading.goodreels')
    time.sleep(1)
    
    print("[2] Spawning app...")
    pid = device.spawn(['com.newreading.goodreels'])
    session = device.attach(pid)
    
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    device.resume(pid)
    
    print("[3] Monitoring for 60 seconds...")
    print("=" * 60)
    print(">>> BROWSE THE APP NOW! <<<")
    print(">>> Wait for home to load, then tap a drama <<<")
    print("=" * 60)
    
    try:
        time.sleep(60)
    except KeyboardInterrupt:
        print("\n[!] Stopped")
    
    print("\n[4] Saving...")
    save_data()
    
    # Print important headers
    print("\n" + "=" * 60)
    print("KEY HEADERS CAPTURED:")
    print("=" * 60)
    for key in ['sign', 'timestamp', 'Authorization', 'deviceId', 'androidId', 'userId']:
        if key in captured_headers:
            print(f"  {key}: {str(captured_headers[key])[:80]}...")
    
    print("\n=== Done ===")

if __name__ == '__main__':
    main()
