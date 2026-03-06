"""
RETROFIT RESPONSE HOOK - Target Retrofit's GsonConverterFactory
Since app uses Retrofit + Gson, hook at the conversion layer
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
            ptype = payload.get('type', '')
            if ptype in ['retrofit_response', 'book_data', 'chapter_data', 'video_data', 'api_data']:
                captured.append(payload)
                print(f"\n[{ptype.upper()}] ===")
                data_preview = str(payload)[:300]
                print(data_preview)
        else:
            print(str(payload)[:120])

script_code = """
setTimeout(function() {
    Java.perform(function() {
        send('[*] Retrofit Response Hook');
        
        // Hook Retrofit's GsonResponseBodyConverter
        try {
            var classes = Java.enumerateLoadedClassesSync();
            var converters = classes.filter(function(c) {
                return c.includes('GsonResponseBodyConverter') || 
                       c.includes('retrofit2.converter.gson');
            });
            send('[i] Gson converters: ' + JSON.stringify(converters));
        } catch(e) {}
        
        // Hook at generic level - retrofit2.Response creation
        try {
            var Response = Java.use('retrofit2.Response');
            // success() method returns the response body
            Response.body.implementation = function() {
                var body = this.body();
                if (body) {
                    try {
                        var bodyStr = body.toString();
                        // Check if it's interesting data
                        if (bodyStr.includes('book') || bodyStr.includes('chapter') || 
                            bodyStr.includes('video') || bodyStr.includes('List')) {
                            send({
                                type: 'retrofit_response',
                                code: this.code(),
                                isSuccessful: this.isSuccessful(),
                                bodyPreview: bodyStr.substring(0, 500)
                            });
                        }
                    } catch(e) {}
                }
                return body;
            };
            send('[OK] retrofit2.Response.body hooked');
        } catch(e) {
            send('[!] retrofit2.Response hook failed');
        }
        
        // Hook specific book-related classes
        try {
            var BookModel = Java.use('com.newreading.goodreels.model.BookModel');
            BookModel.$init.overload().implementation = function() {
                send({type: 'book_created'});
                return this.$init();
            };
            send('[OK] BookModel hooked');
        } catch(e) {
            send('[!] BookModel not found');
        }
        
        // Hook book list/home response model
        try {
            // Try to find HomeIndexResponse or similar
            Java.enumerateLoadedClassesSync().forEach(function(className) {
                if (className.includes('com.newreading.goodreels') && 
                    (className.includes('HomeIndex') || 
                     className.includes('BookList') ||
                     className.includes('ChapterList'))) {
                    send({type: 'found_model', name: className});
                }
            });
        } catch(e) {}
        
        // Hook SharedPreferences to capture cached data reads
        try {
            var SharedPreferences = Java.use('android.content.SharedPreferences');
            var Editor = Java.use('android.content.SharedPreferences$Editor');
            
            // Hook getString to see what's being read
            var prefs = Java.use('android.app.SharedPreferencesImpl');
            prefs.getString.implementation = function(key, defValue) {
                var result = this.getString(key, defValue);
                if (key && (key.includes('book') || key.includes('chapter') || 
                           key.includes('cache') || key.includes('drama'))) {
                    send({type: 'pref_read', key: key, valueLen: result ? result.length : 0});
                }
                return result;
            };
            send('[OK] SharedPreferences hooked');
        } catch(e) {}
        
        send('[READY] Now browse the app...');
    });
}, 2000);
"""

def main():
    print("=" * 60)
    print("RETROFIT RESPONSE HOOK SCRAPER")
    print("=" * 60)
    
    result = subprocess.run(['adb', 'shell', 'pidof', 'com.newreading.goodreels'],
                          capture_output=True, text=True)
    pid = int(result.stdout.strip()) if result.stdout.strip() else None
    
    if not pid:
        print("[!] Starting app via spawn...")
        device = frida.get_usb_device()
        pid = device.spawn(['com.newreading.goodreels'])
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
    
    print("\n>>> BROWSE APP - scroll, tap dramas, play videos <<<\n")
    
    try:
        time.sleep(120)  # 2 minutes
    except KeyboardInterrupt:
        pass
    
    session.detach()
    
    print(f"\n[OK] Captured {len(captured)} items")
    
    # Save
    output_dir = Path('scraped_data')
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / 'retrofit_capture.json', 'w', encoding='utf-8') as f:
        json.dump(captured, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Saved to scraped_data/retrofit_capture.json")

if __name__ == '__main__':
    main()
