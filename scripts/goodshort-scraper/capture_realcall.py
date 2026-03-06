"""
Find OkHttp classes and their methods to hook correctly
"""
import frida
import time

def on_message(message, data):
    if message['type'] == 'send':
        print(message['payload'])

script_code = """
setTimeout(function() {
    Java.perform(function() {
        send('=== Finding OkHttp classes ===');
        
        Java.enumerateLoadedClasses({
            onMatch: function(className) {
                if (className.includes('okhttp3.Request')) {
                    send('Found: ' + className);
                    try {
                        var cls = Java.use(className);
                        var methods = cls.class.getDeclaredMethods();
                        methods.forEach(function(m) {
                            send('  - ' + m.getName());
                        });
                    } catch(e) {}
                }
            },
            onComplete: function() {
                send('Search complete');
            }
        });
        
        // Look for the actual request building
        send('');
        send('=== Trying to hook RealCall ===');
        
        try {
            var RealCall = Java.use('okhttp3.internal.connection.RealCall');
            send('RealCall found!');
            
            RealCall.execute.implementation = function() {
                var request = this.request();
                var url = request.url().toString();
                
                if (url.includes('goodreels')) {
                    send('');
                    send('[📡] API CALL: ' + url);
                    
                    var headers = request.headers();
                    var names = headers.names();
                    var iter = names.iterator();
                    
                    while (iter.hasNext()) {
                        var name = iter.next();
                        var value = headers.get(name);
                        
                        // Only log important headers
                        if (name === 'sign' || name === 'timestamp' || 
                            name === 'Authorization' || name === 'deviceId' ||
                            name === 'androidId' || name === 'userId') {
                            send('  ' + name + ': ' + value);
                        }
                    }
                }
                
                return this.execute();
            };
            
            send('RealCall.execute hooked!');
        } catch(e) {
            send('RealCall error: ' + e.message);
        }
        
        // Also try enqueue for async calls
        try {
            var RealCall = Java.use('okhttp3.internal.connection.RealCall');
            
            RealCall.enqueue.implementation = function(callback) {
                var request = this.request();
                var url = request.url().toString();
                
                if (url.includes('goodreels')) {
                    send('');
                    send('[📡 ASYNC] API CALL: ' + url);
                    
                    var headers = request.headers();
                    var sign = headers.get('sign');
                    if (sign) {
                        send('  sign: ' + sign);
                    }
                    
                    var auth = headers.get('Authorization');
                    if (auth) {
                        send('  Authorization: ' + auth.substring(0, 50) + '...');
                    }
                }
                
                return this.enqueue(callback);
            };
            
            send('RealCall.enqueue hooked!');
        } catch(e) {
            send('RealCall.enqueue error: ' + e.message);
        }
        
        send('');
        send('[✅] Ready - browse app to capture API calls');
    });
}, 2000);
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
    
    print("Monitoring API calls for 30 seconds...")
    time.sleep(30)
    
    print("\\n=== Done ===")

if __name__ == '__main__':
    main()
