"""
Capture sign input specifically for /home/index endpoint
Wait for user to trigger home refresh
"""
import frida
import time
import subprocess
import json

captured_inputs = []

def on_message(message, data):
    global captured_inputs
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, dict) and payload.get('type') == 'sign_data':
            captured_inputs.append(payload)
            inp = payload.get('input', '')
            print(f"\n[CAPTURED] Length: {len(inp)}")
            print(f"First 100: {inp[:100]}")
            
            # Check if it's for home/index
            if '"pageNo"' in inp or '"pageSize"' in inp or '"channelType"' in inp:
                print(">>> THIS IS HOME/INDEX REQUEST!")
        else:
            print(str(payload)[:80])

script_code = """
Java.perform(function() {
    send('[*] Waiting for /home/index request...');
    
    var Signature = Java.use('java.security.Signature');
    
    Signature.update.overload('[B').implementation = function(data) {
        var bytes = Java.array('byte', data);
        var str = '';
        for (var i = 0; i < bytes.length; i++) {
            str += String.fromCharCode(bytes[i] & 0xff);
        }
        
        if (str.includes('timestamp=')) {
            send({
                type: 'sign_data',
                input: str,
                length: bytes.length
            });
        }
        
        return this.update(data);
    };
    
    send('[OK] Hook ready - now pull-to-refresh in the app!');
});
"""

def main():
    print("=" * 60)
    print("CAPTURE /home/index SIGN INPUT")
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
    
    print("\n" + "=" * 60)
    print(">>> PULL DOWN TO REFRESH HOME PAGE <<<")
    print(">>> OR TAP HOME TAB <<<")
    print("=" * 60)
    print("\nWaiting 60 seconds...")
    
    try:
        time.sleep(60)
    except KeyboardInterrupt:
        pass
    
    session.detach()
    
    print("\n" + "=" * 60)
    print(f"CAPTURED {len(captured_inputs)} INPUTS")
    print("=" * 60)
    
    # Find home/index one
    for i, cap in enumerate(captured_inputs):
        inp = cap['input']
        if '"pageNo"' in inp or '"pageSize"' in inp:
            print(f"\nHome/Index input found (#{i+1}):")
            print(f"Length: {len(inp)}")
            print("\nFull input:")
            print(inp)
            
            with open('home_index_input.txt', 'w', encoding='utf-8') as f:
                f.write(inp)
            print("\n[Saved to home_index_input.txt]")
            break
    
    # Save all
    with open('all_captured_inputs.json', 'w', encoding='utf-8') as f:
        json.dump(captured_inputs, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    main()
