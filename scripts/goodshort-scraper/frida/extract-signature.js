/**
 * Improved Frida Hook - Direct Signature MD5 Extraction
 * 
 * This script directly hooks the NRKeyManager.getKey() method
 * to capture the COMPLETE input string including APK signature MD5
 */

Java.perform(function () {
    console.log('\n[*] Hooking NRKeyManager.getKey() for complete input capture...\n');

    try {
        const NRKeyManager = Java.use('ae.b'); // Obfuscated class name for NRKeyManager

        NRKeyManager.getKey.overload('android.content.Context', 'java.lang.String').implementation = function (context, input) {
            console.log('\n========================================');
            console.log('[🔐] NRKeyManager.getKey() CALLED!');
            console.log('========================================');
            console.log('Input String (raw):', input);
            console.log('Input Length:', input.length);
            console.log('');

            // Call original to get d.a(context) appended
            const result = this.getKey(context, input);

            console.log('Generated Sign:', result.substring(0, 60) + '...');
            console.log('========================================\n');

            return result;
        };

        console.log('[✓] Hooked NRKeyManager.getKey()');
        console.log('[i] Now browse the app to trigger sign generation!');
        console.log('[i] The complete input (with APK signature MD5) will be logged.\n');

    } catch (e) {
        console.log('[!] Failed to hook NRKeyManager:', e.message);
        console.log('[!] Trying alternative class names...\n');

        // Try alternative approach - hook class 'd'
        try {
            const ClassD = Java.use('ae.d');

            ClassD.a.overload('android.content.Context').implementation = function (context) {
                const result = this.a(context);
                console.log('\n[+] APK Signature MD5 (from d.a):', result);
                console.log('[✓] Copy this value for API testing!\n');
                return result;
            };

            console.log('[✓] Hooked d.a(Context) as fallback');
        } catch (e2) {
            console.log('[!] Fallback also failed:', e2.message);
        }
    }

    console.log('\n[i] Script ready. Use the app to trigger hooks.\n');
});
