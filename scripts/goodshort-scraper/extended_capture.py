"""
EXTENDED CAPTURE - 5 minutes for thorough browsing
"""
import frida
import json
import time
from pathlib import Path

captured = []

def on_message(message, data):
    global captured
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, dict):
            ptype = payload.get('type', '')
            captured.append(payload)
            if ptype not in ['log']:
                preview = str(payload).replace('\n', ' ')[:100]
                print(f"[{ptype}] {preview}...")
        else:
            print(str(payload)[:80])

script_code = """
setTimeout(function() {
    Java.perform(function() {
        send({type: 'log', msg: 'Extended Capture Starting'});
        
        // Retrofit response
        try {
            var Response = Java.use('retrofit2.Response');
            Response.body.implementation = function() {
                var body = this.body();
                if (body) {
                    try {
                        var s = body.toString();
                        if (s.length > 10) {
                            send({type: 'response', code: this.code(), bodyLen: s.length, body: s.substring(0, 2000)});
                        }
                    } catch(e) {}
                }
                return body;
            };
            send({type: 'log', msg: 'Retrofit hooked'});
        } catch(e) {}
        
        // JSON parsing  
        try {
            var JSONObject = Java.use('org.json.JSONObject');
            JSONObject.$init.overload('java.lang.String').implementation = function(str) {
                var s = str ? str.toString() : '';
                if (s.length > 50 && (s.includes('"success"') || s.includes('"data"') || s.includes('"bookId"'))) {
                    send({type: 'json', length: s.length, preview: s.substring(0, 2000)});
                }
                return this.$init(str);
            };
            send({type: 'log', msg: 'JSONObject hooked'});
        } catch(e) {}
        
        // URL captures for videos
        try {
            var URL = Java.use('java.net.URL');
            URL.$init.overload('java.lang.String').implementation = function(urlStr) {
                var s = urlStr ? urlStr.toString() : '';
                if (s.includes('.ts') || s.includes('.m3u8') || s.includes('goodreels.com/mts')) {
                    send({type: 'video_url', url: s});
                }
                return this.$init(urlStr);
            };
            send({type: 'log', msg: 'URL hooked'});
        } catch(e) {}
        
        send({type: 'log', msg: 'All hooks ready!'});
    });
}, 3000);
"""

def main():
    print("=" * 60)
    print("EXTENDED CAPTURE - 5 MINUTES")
    print("=" * 60)
    
    device = frida.get_usb_device()
    
    print("\n[1] Spawning app...")
    pid = device.spawn(['com.newreading.goodreels'])
    print(f"    PID: {pid}")
    
    print("[2] Attaching hooks...")
    session = device.attach(pid)
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    print("[3] Resuming app...")
    device.resume(pid)
    
    print("\n" + "=" * 60)
    print(">>> LOGIN, THEN BROWSE EXTENSIVELY <<<")
    print("- Scroll home page all the way")
    print("- Tap 5-10 different dramas")
    print("- Play a few video episodes")
    print("- Visit different categories")
    print("=" * 60)
    print("\nCapturing for 5 MINUTES...")
    
    try:
        time.sleep(300)  # 5 minutes
    except KeyboardInterrupt:
        print("\n[!] Stopped early")
    
    session.detach()
    
    # Summary
    responses = [c for c in captured if c.get('type') == 'response']
    jsons = [c for c in captured if c.get('type') == 'json']
    videos = [c for c in captured if c.get('type') == 'video_url']
    
    print(f"\n" + "=" * 60)
    print(f"CAPTURE COMPLETE!")
    print(f"- Responses: {len(responses)}")
    print(f"- JSON payloads: {len(jsons)}")
    print(f"- Video URLs: {len(videos)}")
    print(f"- Total: {len(captured)}")
    print("=" * 60)
    
    # Save
    output_dir = Path('scraped_data')
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / 'extended_capture.json', 'w', encoding='utf-8') as f:
        json.dump(captured, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Saved to scraped_data/extended_capture.json")

if __name__ == '__main__':
    main()
