"""
DEEP DEBUG - Hook Java Signature class to see EXACT bytes being signed
This is the lowest level before native code - will reveal exact signing input
"""
import frida
import time
import subprocess
import base64

signing_data = []

def on_message(message, data):
    global signing_data
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, dict) and payload.get('type') == 'sign_input':
            signing_data.append(payload)
            input_str = payload.get('input', '')
            print(f"\n[SIGN INPUT] Length: {len(input_str)}")
            print(f"First 200 chars: {input_str[:200]}")
            print(f"Last 100 chars: ...{input_str[-100:]}")
        else:
            print(str(payload)[:150])

script_code = """
Java.perform(function() {
    send('[*] Deep Signature Debugging');
    
    // Hook java.security.Signature - this is where RSA signing happens
    var Signature = Java.use('java.security.Signature');
    
    // Hook update method - this is where data is fed for signing
    Signature.update.overload('[B').implementation = function(data) {
        var bytes = Java.array('byte', data);
        var str = '';
        for (var i = 0; i < bytes.length; i++) {
            str += String.fromCharCode(bytes[i] & 0xff);
        }
        
        // Only log if it looks like our sign input (contains path or timestamp patterns)
        if (str.includes('/home') || str.includes('/chapter') || 
            str.includes('goodreels') || str.length > 100) {
            send({
                type: 'sign_input',
                input: str,
                length: bytes.length
            });
        }
        
        return this.update(data);
    };
    
    // Also hook the overload that takes offset and length
    Signature.update.overload('[B', 'int', 'int').implementation = function(data, off, len) {
        var bytes = Java.array('byte', data);
        var str = '';
        for (var i = off; i < off + len && i < bytes.length; i++) {
            str += String.fromCharCode(bytes[i] & 0xff);
        }
        
        if (str.includes('/home') || str.includes('/chapter') || 
            str.includes('goodreels') || str.length > 100) {
            send({
                type: 'sign_input',
                input: str,
                length: len
            });
        }
        
        return this.update(data, off, len);
    };
    
    send('[OK] Signature.update hooked');
    
    // Also hook sign() to see the output
    Signature.sign.overload().implementation = function() {
        send('[SIGN] Signature.sign() called');
        var result = this.sign();
        var b64 = Java.use('android.util.Base64').encodeToString(result, 0);
        send('[SIGN] Result: ' + b64.substring(0, 60) + '...');
        return result;
    };
    
    send('[OK] Signature.sign hooked');
    send('');
    send('[READY] Now trigger an API call in the app (scroll/tap)...');
});
"""

def main():
    print("=" * 60)
    print("DEEP SIGNATURE DEBUGGING")
    print("=" * 60)
    
    result = subprocess.run(['adb', 'shell', 'pidof', 'com.newreading.goodreels'],
                          capture_output=True, text=True)
    pid = int(result.stdout.strip()) if result.stdout.strip() else None
    
    if not pid:
        print("[!] App not running!")
        return
    
    print(f"[OK] App PID: {pid}")
    
    device = frida.get_usb_device()
    session = device.attach(pid)
    
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    print("\n" + "=" * 60)
    print(">>> SCROLL/TAP IN APP TO TRIGGER API CALL <<<")
    print("=" * 60)
    print("\nWaiting for sign operations (60 seconds)...")
    
    try:
        time.sleep(60)
    except KeyboardInterrupt:
        pass
    
    print("\n" + "=" * 60)
    if signing_data:
        print(f"CAPTURED {len(signing_data)} SIGNING OPERATIONS")
        print("=" * 60)
        
        # Save to file
        with open('sign_inputs.txt', 'w', encoding='utf-8') as f:
            for i, data in enumerate(signing_data):
                f.write(f"=== Sign Input {i+1} ===\n")
                f.write(f"Length: {data.get('length')}\n")
                f.write(f"Input:\n{data.get('input')}\n\n")
        
        print("Saved to sign_inputs.txt")
        
        # Analyze first input
        if signing_data:
            first = signing_data[0]['input']
            print("\nFIRST SIGN INPUT ANALYSIS:")
            print(f"  Total length: {len(first)}")
            
            # Try to identify components
            parts = first.split('com.newreading.goodreels')
            if len(parts) > 1:
                print(f"  Before package name: {parts[0][:100]}...")
                print(f"  After package name: {parts[1][:50] if len(parts[1]) > 0 else '(empty)'}")
    else:
        print("NO SIGNING OPERATIONS CAPTURED!")
        print("The app might be using cached data or different signing method")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
