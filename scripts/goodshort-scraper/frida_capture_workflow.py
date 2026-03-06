"""
FRIDA CAPTURE WORKFLOW - Intercept COMPLETE HTTP requests from GoodShort app

This script captures ALL headers from actual API calls made by the app,
then saves them to a JSON file for replay in our scraper.
"""
import frida
import json
import time
import os
from datetime import datetime

# Store captured requests
captured_requests = []

def on_message(message, data):
    global captured_requests
    if message['type'] == 'send':
        payload = message['payload']
        
        # Check if it's a captured request
        if isinstance(payload, dict) and payload.get('type') == 'request':
            captured_requests.append(payload)
            print(f"\n[📡] Captured: {payload.get('method')} {payload.get('url')}")
            print(f"    Headers: {len(payload.get('headers', {}))} items")
        elif isinstance(payload, str):
            print(payload)
    elif message['type'] == 'error':
        print(f"[ERROR] {message.get('stack', message)}")

script_code = """
Java.perform(function() {
    send('[*] GoodShort Full Request Capture v1.0');
    send('[*] Waiting for API calls...');
    
    // Store captured headers for each request
    var capturedRequests = [];
    
    // Hook OkHttp Interceptor to capture EVERYTHING
    try {
        // Find all Interceptor implementations
        var Interceptor = Java.use('okhttp3.Interceptor');
        var Chain = Java.use('okhttp3.Interceptor$Chain');
        
        // Hook Request.headers() to capture when headers are read
        var Request = Java.use('okhttp3.Request');
        Request.headers.implementation = function() {
            var headers = this.headers();
            var url = this.url().toString();
            
            if (url.includes('goodreels.com') && url.includes('/hwycclientreels/')) {
                send('[🎯] Intercepting request to: ' + url);
                
                var headerMap = {};
                var names = headers.names();
                var iter = names.iterator();
                
                while (iter.hasNext()) {
                    var name = iter.next();
                    headerMap[name] = headers.get(name);
                }
                
                // Send captured request
                send({
                    type: 'request',
                    url: url,
                    method: this.method(),
                    headers: headerMap,
                    timestamp: Date.now()
                });
            }
            
            return headers;
        };
        
        send('[✓] Request.headers hooked');
    } catch(e) {
        send('[!] Request.headers hook failed: ' + e.message);
    }
    
    // Also hook at Call level
    try {
        var RealCall = Java.use('okhttp3.internal.connection.RealCall');
        
        RealCall.getResponseWithInterceptorChain$okhttp.implementation = function() {
            var request = this.request();
            var url = request.url().toString();
            
            if (url.includes('goodreels.com') && url.includes('/hwycclientreels/')) {
                send('[📤] Outgoing request: ' + url);
                
                var headers = request.headers();
                var headerMap = {};
                var names = headers.names();
                var iter = names.iterator();
                
                while (iter.hasNext()) {
                    var name = iter.next();
                    headerMap[name] = headers.get(name);
                }
                
                send({
                    type: 'request',
                    url: url,
                    method: request.method(),
                    headers: headerMap,
                    timestamp: Date.now()
                });
            }
            
            return this.getResponseWithInterceptorChain$okhttp();
        };
        
        send('[✓] RealCall interceptor hooked');
    } catch(e) {
        send('[!] RealCall hook failed: ' + e.message);
    }
    
    // Fallback: Hook Headers.Builder to capture as headers are added
    try {
        var HeadersBuilder = Java.use('okhttp3.Headers$Builder');
        var currentHeaders = {};
        var currentUrl = '';
        
        HeadersBuilder.add.overload('java.lang.String', 'java.lang.String').implementation = function(name, value) {
            // Track important headers
            if (name === 'sign' || name === 'timestamp' || name === 'Authorization' ||
                name === 'deviceId' || name === 'androidId' || name === 'userId' ||
                name === 'pname' || name === 'platform') {
                currentHeaders[name] = value;
                
                if (name === 'sign') {
                    send('[🔐] Sign header captured: ' + value.substring(0, 50) + '...');
                }
            }
            
            return this.add(name, value);
        };
        
        send('[✓] Headers.Builder hooked');
    } catch(e) {
        send('[!] Headers.Builder hook failed: ' + e.message);
    }
    
    send('');
    send('[✅] All hooks ready! Now browse the app to trigger API calls...');
    send('[i] Scroll the home page, tap on dramas, play videos');
});
"""

def save_captured_requests(requests, filename='captured_requests.json'):
    """Save captured requests to JSON file"""
    output = {
        'capturedAt': datetime.now().isoformat(),
        'count': len(requests),
        'requests': requests
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n[💾] Saved {len(requests)} requests to {filename}")

def main():
    global captured_requests
    
    print("=" * 60)
    print("GOODSHORT FRIDA CAPTURE WORKFLOW")
    print("=" * 60)
    
    device = frida.get_usb_device()
    
    # Clear app data for fresh state
    print("\n[1/4] Clearing app data...")
    os.system('adb shell pm clear com.newreading.goodreels')
    time.sleep(1)
    
    print("[2/4] Spawning app with Frida...")
    pid = device.spawn(['com.newreading.goodreels'])
    session = device.attach(pid)
    
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    device.resume(pid)
    
    print("[3/4] Monitoring for 45 seconds...")
    print("=" * 60)
    print(">>> BROWSE THE APP NOW! <<<")
    print(">>> Scroll home, tap dramas, play videos <<<")
    print("=" * 60)
    
    try:
        time.sleep(45)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
    
    print("\n[4/4] Saving captured requests...")
    
    if captured_requests:
        save_captured_requests(captured_requests)
        
        # Also print summary
        print("\n" + "=" * 60)
        print("CAPTURE SUMMARY")
        print("=" * 60)
        
        for i, req in enumerate(captured_requests[:5]):  # Show first 5
            print(f"\n[{i+1}] {req.get('method')} {req.get('url', '')[:60]}...")
            headers = req.get('headers', {})
            if 'sign' in headers:
                print(f"    sign: {headers['sign'][:50]}...")
            if 'Authorization' in headers:
                print(f"    Authorization: {headers['Authorization'][:50]}...")
    else:
        print("[!] No requests captured!")
        print("[?] Make sure to browse the app after it opens")
    
    print("\n=== Done ===")

if __name__ == '__main__':
    main()
