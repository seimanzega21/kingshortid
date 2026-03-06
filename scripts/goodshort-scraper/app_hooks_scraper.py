"""
APP-SPECIFIC HOOKS - Target known classes from decompilation
Focus on capturing both requests AND responses at app-level
"""
import frida
import json
import time
import subprocess
from pathlib import Path

captured = []

def on_message(message, data):
    global captured
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, dict):
            captured.append(payload)
            ptype = payload.get('type', '')
            print(f"[{ptype}] {str(payload)[:100]}...")
        else:
            print(str(payload)[:100])

script_code = """
Java.perform(function() {
    send('[*] App-Specific Hook Scraper');
    
    // Hook getH5HeaderData - we know this works
    try {
        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');
        AppUtils.getH5HeaderData.implementation = function(timestamp, path) {
            send({type: 'h5_header', timestamp: timestamp, path: path});
            return this.getH5HeaderData(timestamp, path);
        };
        send('[OK] AppUtils.getH5HeaderData hooked');
    } catch(e) {
        send('[!] getH5HeaderData failed: ' + e.message);
    }
    
    // Hook okhttp3.Callback onResponse - async response handler
    try {
        var reallyAny = Java.enumerateLoadedClassesSync().filter(function(c) {
            return c.includes('okhttp');
        });
        send('[i] OkHttp classes: ' + reallyAny.length);
        
        // Try to find all classes implementing Callback
        Java.enumerateLoadedClassesSync().forEach(function(className) {
            if (className.includes('Callback') && className.includes('okhttp')) {
                send('[i] Found: ' + className);
            }
        });
    } catch(e) {}
    
    // Hook at Retrofit level if exists
    try {
        var ServiceMethod = Java.use('retrofit2.ServiceMethod');
        send('[i] Retrofit ServiceMethod found');
    } catch(e) {}
    
    // Hook any class with "Response" in name from goodreels package  
    try {
        Java.enumerateLoadedClassesSync().forEach(function(className) {
            if (className.includes('com.newreading.goodreels') && 
                (className.includes('Response') || className.includes('Result'))) {
                send({type: 'found_class', name: className});
            }
        });
    } catch(e) {}
    
    // Hook shared preferences for token
    try {
        var SpData = Java.use('com.newreading.goodreels.utils.SpData');
        SpData.getUserId.implementation = function() {
            var result = this.getUserId();
            send({type: 'user_id', value: result ? result.toString() : 'null'});
            return result;
        };
        send('[OK] SpData.getUserId hooked');
    } catch(e) {}
    
    send('');
    send('[READY] Browse app now - looking for response classes...');
});
"""

def main():
    print("=" * 60)
    print("APP-SPECIFIC HOOK SCRAPER")
    print("=" * 60)
    
    result = subprocess.run(['adb', 'shell', 'pidof', 'com.newreading.goodreels'],
                          capture_output=True, text=True)
    pid = int(result.stdout.strip()) if result.stdout.strip() else None
    
    if not pid:
        print("[!] App not running! Starting...")
        device = frida.get_usb_device()
        pid = device.spawn(['com.newreading.goodreels'])
        print(f"[OK] Spawned PID: {pid}")
        session = device.attach(pid)
        script = session.create_script(script_code)
        script.on('message', on_message)
        script.load()
        device.resume(pid)
    else:
        print(f"[OK] Attaching to PID: {pid}")
        device = frida.get_usb_device()
        session = device.attach(pid)
        script = session.create_script(script_code)
        script.on('message', on_message)
        script.load()
    
    print("\n>>> BROWSE APP NOW <<<\n")
    
    try:
        time.sleep(60)
    except KeyboardInterrupt:
        pass
    
    session.detach()
    
    # Analyze and save
    print(f"\n[OK] Captured {len(captured)} items")
    
    response_classes = [c for c in captured if c.get('type') == 'found_class']
    h5_headers = [c for c in captured if c.get('type') == 'h5_header']
    
    print(f"\n--- Response/Result classes found: {len(response_classes)} ---")
    for c in response_classes[:20]:
        print(f"  {c.get('name')}")
    
    print(f"\n--- getH5HeaderData calls: {len(h5_headers)} ---")
    for h in h5_headers[:10]:
        print(f"  path: {h.get('path')}")
    
    # Save
    output_dir = Path('scraped_data')
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / 'app_hooks.json', 'w', encoding='utf-8') as f:
        json.dump(captured, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    main()
