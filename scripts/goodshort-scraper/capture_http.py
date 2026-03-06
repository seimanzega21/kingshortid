"""
Capture ACTUAL HTTP request made by the app - intercept at network level
"""
import frida
import time

def on_message(message, data):
    if message['type'] == 'send':
        print(message['payload'])
    elif message['type'] == 'error':
        print(f"[ERROR] {message['stack']}")

script_code = """
Java.perform(function() {
    send('[*] Intercepting OkHttp requests...');
    
    // Hook OkHttp3's internal classes
    try {
        var Builder = Java.use('okhttp3.Request$Builder');
        
        // Intercept all headers being added
        Builder.addHeader.implementation = function(name, value) {
            if (name.toLowerCase() === 'sign' || 
                name.toLowerCase() === 'timestamp' ||
                name.toLowerCase() === 'authorization' ||
                name.toLowerCase() === 'deviceid' ||
                name.toLowerCase() === 'androidid' ||
                name.toLowerCase() === 'userid') {
                send('[HEADER] ' + name + ': ' + value);
            }
            return this.addHeader(name, value);
        };
        
        Builder.header.implementation = function(name, value) {
            if (name.toLowerCase() === 'sign' || 
                name.toLowerCase() === 'timestamp' ||
                name.toLowerCase() === 'authorization') {
                send('[HEADER] ' + name + ': ' + value);
            }
            return this.header(name, value);
        };
        
        send('[✓] OkHttp Request.Builder hooked');
    } catch(e) {
        send('[!] OkHttp hook failed: ' + e.message);
    }
    
    // Also hook URL to see what endpoint is called
    try {
        var HttpUrl = Java.use('okhttp3.HttpUrl');
        HttpUrl.toString.implementation = function() {
            var url = this.toString();
            if (url.includes('goodreels.com')) {
                send('[URL] ' + url);
            }
            return url;
        };
        send('[✓] HttpUrl hooked');
    } catch(e) {
        send('[!] HttpUrl hook failed: ' + e.message);
    }
    
    send('[✅] Ready! Now browse the app to see API calls...');
});
"""

def main():
    device = frida.get_usb_device()
    
    print("Spawning app...")
    pid = device.spawn(['com.newreading.goodreels'])
    session = device.attach(pid)
    
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    device.resume(pid)
    
    print("Waiting for API calls (browse the app!)...")
    time.sleep(30)  # Wait longer for user interaction
    
    print("\\n=== Done ===")

if __name__ == '__main__':
    main()
