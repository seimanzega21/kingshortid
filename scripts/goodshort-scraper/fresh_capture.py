"""
FRESH START CAPTURE - After cache clear, capture all API responses
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
                print(f"[{ptype}] {str(payload)[:120]}...")
        else:
            print(str(payload)[:100])

script_code = """
setTimeout(function() {
    Java.perform(function() {
        send({type: 'log', msg: 'Fresh Start Capture'});
        
        // Hook Retrofit response
        try {
            var Response = Java.use('retrofit2.Response');
            Response.body.implementation = function() {
                var body = this.body();
                if (body) {
                    try {
                        var s = body.toString();
                        if (s.length > 10) {
                            send({type: 'response', code: this.code(), body: s.substring(0, 1000)});
                        }
                    } catch(e) {}
                }
                return body;
            };
            send({type: 'log', msg: 'Retrofit hooked'});
        } catch(e) {}
        
        // Hook OkHttp Interceptor
        try {
            var Interceptor = Java.use('okhttp3.Interceptor$Chain');
            send({type: 'log', msg: 'Interceptor class found'});
        } catch(e) {}
        
        // Hook JSON parsing  
        try {
            var JSONObject = Java.use('org.json.JSONObject');
            JSONObject.$init.overload('java.lang.String').implementation = function(str) {
                var s = str ? str.toString() : '';
                if (s.length > 50 && (s.includes('"success"') || s.includes('"data"'))) {
                    send({type: 'json', length: s.length, preview: s.substring(0, 500)});
                }
                return this.$init(str);
            };
            send({type: 'log', msg: 'JSONObject hooked'});
        } catch(e) {}
        
        // Hook Gson Type adapter
        try {
            var GsonBuilder = Java.use('com.google.gson.GsonBuilder');
            GsonBuilder.create.implementation = function() {
                send({type: 'log', msg: 'Gson created'});
                return this.create();
            };
            send({type: 'log', msg: 'GsonBuilder hooked'});
        } catch(e) {}
        
        send({type: 'log', msg: 'All hooks ready!'});
    });
}, 3000);
"""

def main():
    print("=" * 60)
    print("FRESH START CAPTURE (after cache clear)")
    print("=" * 60)
    
    device = frida.get_usb_device()
    
    print("\n[1] Spawning fresh app...")
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
    print(">>> APP STARTING FRESH <<<")
    print(">>> Login if needed, then scroll <<<")
    print("=" * 60)
    print("\nWaiting 3 minutes...")
    
    try:
        time.sleep(180)
    except KeyboardInterrupt:
        pass
    
    session.detach()
    
    # Analyze
    responses = [c for c in captured if c.get('type') in ['response', 'json']]
    logs = [c for c in captured if c.get('type') == 'log']
    
    print(f"\n[OK] Logs: {len(logs)}, Responses: {len(responses)}")
    
    # Save
    output_dir = Path('scraped_data')
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / 'fresh_capture.json', 'w', encoding='utf-8') as f:
        json.dump(captured, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Saved to scraped_data/fresh_capture.json")
    
    if responses:
        print("\n--- Sample Responses ---")
        for r in responses[:5]:
            preview = str(r)[:200]
            print(preview)
            print()

if __name__ == '__main__':
    main()
