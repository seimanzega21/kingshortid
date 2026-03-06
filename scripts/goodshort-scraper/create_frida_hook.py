"""
Frida script to hook signing function at runtime
This captures the signing process without needing to reverse engineer
"""

FRIDA_SCRIPT = """
// GoodShort Request Signing Hook
// Captures signing logic at runtime

console.log('[*] GoodShort Signing Hook Started');

// Hook common signing methods
Java.perform(function() {
    console.log('[*] Java environment loaded');
    
    // Common class names for signing
    var signingClassPatterns = [
        'com.newreading.goodreels.sign',
        'com.newreading.goodreels.security',
        'com.newreading.goodreels.crypto',
        'com.newreading.goodreels.util.sign',
        'com.newreading.common.sign'
    ];
    
    // Try to find signing classes
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            // Look for signing-related classes
            if (className.toLowerCase().includes('sign') && 
                (className.includes('newreading') || className.includes('goodreels'))) {
                console.log('[+] Found potential signing class: ' + className);
                
                try {
                    var SignClass = Java.use(className);
                    
                    // List all methods
                    var methods = SignClass.class.getDeclaredMethods();
                    methods.forEach(function(method) {
                        console.log('    Method: ' + method.toString());
                    });
                    
                } catch (e) {
                    // Skip if can't load
                }
            }
        },
        onComplete: function() {
            console.log('[*] Class enumeration complete');
        }
    });
    
    // Hook Signature class (standard Java crypto)
    try {
        var Signature = Java.use('java.security.Signature');
        
        Signature.getInstance.overload('java.lang.String').implementation = function(algorithm) {
            console.log('[SIGNATURE] Algorithm requested: ' + algorithm);
            return this.getInstance(algorithm);
        };
        
        Signature.update.overload('[B').implementation = function(data) {
            console.log('[SIGNATURE] Data to sign (bytes): ' + data.length + ' bytes');
            console.log('[SIGNATURE] Data (hex): ' + bytesToHex(data).substring(0, 200));
            console.log('[SIGNATURE] Data (string): ' + bytesToString(data).substring(0, 200));
            return this.update(data);
        };
        
        Signature.sign.overload().implementation = function() {
            var result = this.sign();
            console.log('[SIGNATURE] Generated signature: ' + bytesToBase64(result));
            return result;
        };
        
        console.log('[+] Hooked Signature class');
        
    } catch (e) {
        console.log('[-] Failed to hook Signature: ' + e);
    }
    
    // Hook OkHttp interceptors (where sign header is added)
    try {
        var Interceptor = Java.use('okhttp3.Interceptor');
        console.log('[+] Found OkHttp Interceptor');
        
        // This will catch all custom in terceptors
        Java.choose('okhttp3.Interceptor', {
            onMatch: function(instance) {
                console.log('[+] Found Interceptor instance: ' + instance.$className);
            },
            onComplete: function() {}
        });
        
    } catch (e) {
        console.log('[-] OkHttp not found: ' + e);
    }
    
    // Helper functions
    function bytesToHex(bytes) {
        var hex = '';
        for (var i = 0; i < bytes.length; i++) {
            hex += ('0' + (bytes[i] & 0xFF).toString(16)).slice(-2);
        }
        return hex;
    }
    
    function bytesToString(bytes) {
        return Java.use('java.lang.String').$new(bytes);
    }
    
    function bytesToBase64(bytes) {
        return Java.use('android.util.Base64').encodeToString(bytes, 0);
    }
    
    console.log('[*] All hooks installed');
    console.log('[*] Now make some API requests in the app...');
});
"""

def save_frida_script():
    """Save Frida script to file"""
    
    with open('frida_sign_hook.js', 'w', encoding='utf-8') as f:
        f.write(FRIDA_SCRIPT)
    
    print("✅ Saved Frida script: frida_sign_hook.js\n")
    print("To run:")
    print("  1. Make sure Frida server is running on LDPlayer")
    print("  2. frida -U -f com.newreading.goodreels -l frida_sign_hook.js")
    print("  3. Use the app to make requests")
    print("  4. Check console for signing details\n")


if __name__ == "__main__":
    save_frida_script()
