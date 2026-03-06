"""
Capture CLEAN sign input by calling getSign directly via Frida
Then compare byte-by-byte with our generator
"""
import frida
import time
import subprocess
import json

captured_input = None

def on_message(message, data):
    global captured_input
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, dict) and payload.get('type') == 'sign_data':
            captured_input = payload
            print("[OK] Captured sign input data!")
        else:
            print(str(payload)[:100])

script_code = """
Java.perform(function() {
    send('[*] Hooking to capture exact sign input...');
    
    // Hook Signature.update to capture the bytes
    var Signature = Java.use('java.security.Signature');
    
    Signature.update.overload('[B').implementation = function(data) {
        var bytes = Java.array('byte', data);
        var str = '';
        for (var i = 0; i < bytes.length; i++) {
            str += String.fromCharCode(bytes[i] & 0xff);
        }
        
        // Only capture if it looks like our target
        if (str.includes('timestamp=')) {
            send({
                type: 'sign_data',
                input: str,
                length: bytes.length,
                hex: Array.from(bytes).map(function(b) { return (b & 0xff).toString(16).padStart(2, '0'); }).join('')
            });
        }
        
        return this.update(data);
    };
    
    send('[OK] Hook ready');
    
    // Trigger a sign call
    var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');
    var ts = Date.now().toString();
    
    send('[*] Triggering getSign with ts=' + ts);
    var sign = AppUtils.getSign(ts, '/home/index');
    send('[OK] Sign generated');
});
"""

def main():
    global captured_input
    
    print("=" * 60)
    print("CLEAN SIGN INPUT CAPTURE")
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
    
    # Wait for capture
    for _ in range(20):
        if captured_input:
            break
        time.sleep(0.5)
    
    session.detach()
    
    if captured_input:
        print("\n" + "=" * 60)
        print("CAPTURED INPUT")
        print("=" * 60)
        inp = captured_input['input']
        print(f"Length: {len(inp)}")
        print(f"\nFull input:")
        print(inp)
        
        # Save to file
        with open('exact_sign_input.txt', 'w', encoding='utf-8') as f:
            f.write(inp)
        
        with open('exact_sign_input.json', 'w', encoding='utf-8') as f:
            json.dump(captured_input, f, indent=2)
        
        print("\n[OK] Saved to exact_sign_input.txt and .json")
    else:
        print("[!] No input captured")

if __name__ == '__main__':
    main()
