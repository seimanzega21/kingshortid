"""
Enhanced Frida script to capture EVERYTHING about signing
"""

FRIDA_SCRIPT = """
console.log('[*] ===================================');
console.log('[*] GoodShort Signing Capture Started');
console.log('[*] ===================================');

Java.perform(function() {
    console.log('[*] Java environment ready');
    
    // ==========================================
    // STRATEGY 1: Find ALL signing-related classes
    // ==========================================
    
    console.log('[*] Enumerating loaded classes...');
    
    var signingClasses = [];
    
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            var lowerName = className.toLowerCase();
            
            // Look for signing-related keywords
            if ((lowerName.includes('sign') || 
                 lowerName.includes('crypto') || 
                 lowerName.includes('encrypt') ||
                 lowerName.includes('security')) &&
                (lowerName.includes('goodreels') || 
                 lowerName.includes('newreading') ||
                 lowerName.includes('hwyclient'))) {
                
                signingClasses.push(className);
                console.log('[+] FOUND: ' + className);
            }
        },
        onComplete: function() {
            console.log('[*] Class enumeration complete');
            console.log('[*] Found ' + signingClasses.length + ' potential signing classes');
            
            // Try to hook methods in these classes
            signingClasses.forEach(function(className) {
                try {
                    hookSigningClass(className);
                } catch (e) {
                    console.log('[-] Could not hook ' + className + ': ' + e);
                }
            });
        }
    });
    
    // ==========================================
    // STRATEGY 2: Hook standard crypto APIs
    // ==========================================
    
    console.log('[*] Hooking standard Java crypto...');
    
    try {
        var Signature = Java.use('java.security.Signature');
        
        // Hook getInstance
        Signature.getInstance.overload('java.lang.String').implementation = function(algorithm) {
            console.log('\\n[CRYPTO] Signature.getInstance("' + algorithm + '")');
            return this.getInstance(algorithm);
        };
        
        // Hook update (data being signed)
        Signature.update.overload('[B').implementation = function(data) {
            var dataStr = bytesToString(data);
            var dataHex = bytesToHex(data);
            
            console.log('[CRYPTO] Data to sign:');
            console.log('  Length: ' + data.length + ' bytes');
            console.log('  String: ' + dataStr.substring(0, 500));
            console.log('  Hex: ' + dataHex.substring(0, 200));
            
            // Save to file for analysis
            saveToFile('signing_data.txt', dataStr);
            
            return this.update(data);
        };
        
        // Hook sign (signature generation)
        Signature.sign.overload().implementation = function() {
            var result = this.sign();
            var signature = bytesToBase64(result);
            
            console.log('[CRYPTO] Generated Signature:');
            console.log('  ' + signature);
            console.log('  Length: ' + result.length + ' bytes');
            
            // Save signature
            saveToFile('signature_output.txt', signature);
            
            return result;
        };
        
        console.log('[+] Hooked Signature class');
    } catch (e) {
        console.log('[-] Signature hook failed: ' + e);
    }
    
    // ==========================================
    // STRATEGY 3: Hook OkHttp Request Builder
    // ==========================================
    
    console.log('[*] Hooking OkHttp...');
    
    try {
        var RequestBuilder = Java.use('okhttp3.Request$Builder');
        
        RequestBuilder.addHeader.overload('java.lang.String', 'java.lang.String').implementation = function(name, value) {
            if (name.toLowerCase() === 'sign') {
                console.log('\\n[OKHTTP] *** SIGN HEADER ADDED ***');
                console.log('  Sign: ' + value);
                console.log('  Length: ' + value.length);
                
                // Get stack trace to find where signing happens
                console.log('  Stack trace:');
                Java.perform(function() {
                    var Exception = Java.use('java.lang.Exception');
                    var stack = Exception.$new().getStackTrace();
                    for (var i = 0; i < Math.min(10, stack.length); i++) {
                        console.log('    ' + stack[i].toString());
                    }
                });
                
                saveToFile('sign_header.txt', value);
            }
            
            return this.addHeader(name, value);
        };
        
        console.log('[+] Hooked OkHttp Request.Builder');
    } catch (e) {
        console.log('[-] OkHttp hook failed: ' + e);
    }
    
    // ==========================================
    // STRATEGY 4: Hook specific sign method
    // ==========================================
    
    // Try common package structures
    var possibleSignClasses = [
        'com.newreading.goodreels.network.sign.SignUtils',
        'com.newreading.goodreels.utils.SignUtil',
        'com.newreading.common.network.SignHelper',
        'com.newreading.goodreels.api.Signer',
        'com.hwcc.client.sign.SignatureUtil'
    ];
    
    possibleSignClasses.forEach(function(className) {
        try {
            var SignClass = Java.use(className);
            console.log('[+] Found signing class: ' + className);
            
            // Hook all methods
            var methods = SignClass.class.getDeclaredMethods();
            methods.forEach(function(method) {
                console.log('  Method: ' + method.getName());
            });
            
        } catch (e) {
            // Class doesn't exist
        }
    });
    
    // ==========================================
    // Helper Functions
    // ==========================================
    
    function hookSigningClass(className) {
        var SignClass = Java.use(className);
        var methods = SignClass.class.getDeclaredMethods();
        
        console.log('[*] Hooking ' + className + ' (' + methods.length + ' methods)');
        
        // Hook methods that might be signing
        methods.forEach(function(method) {
            var methodName = method.getName();
            if (methodName.includes('sign') || methodName.includes('encrypt')) {
                console.log('  Hooking: ' + methodName);
                // Hook implementation would go here
            }
        });
    }
    
    function bytesToHex(bytes) {
        var hex = '';
        for (var i = 0; i < Math.min(100, bytes.length); i++) {
            hex += ('0' + (bytes[i] & 0xFF).toString(16)).slice(-2);
        }
        return hex;
    }
    
    function bytesToString(bytes) {
        try {
            return Java.use('java.lang.String').$new(bytes, 'UTF-8');
        } catch (e) {
            return '<conversion failed>';
        }
    }
    
    function bytesToBase64(bytes) {
        return Java.use('android.util.Base64').encodeToString(bytes, 0);
    }
    
    function saveToFile(filename, content) {
        // For logging purposes
        send({type: 'file', name: filename, data: content});
    }
    
    console.log('[*] All hooks installed!');
    console.log('[*] Now use the app to trigger API requests...');
});
"""

# Save script
with open('frida_comprehensive_hook.js', 'w', encoding='utf-8') as f:
    f.write(FRIDA_SCRIPT)

print("✅ Saved: frida_comprehensive_hook.js")
print("\nTo run:")
print("1. Make sure Frida server is running on device")
print("2. frida -U -f com.newreading.goodreels -l frida_comprehensive_hook.js --no-pause")
print("3. Browse dramas in the app")
print("4. Check output for signing details")
