/**
 * Deep Debug - Hook ACTUAL sign generation
 * Capture the exact input string used by the app
 */

Java.perform(function () {
    console.log('\n[*] Deep Debug: Hooking Sign Generation...\n');

    try {
        // Hook AppUtils.getSign() to see input
        const AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        const getSign = AppUtils.getSign.overload('java.lang.String', 'java.lang.String');
        getSign.implementation = function (timestamp, path) {
            console.log('\n========================================');
            console.log('[📝] AppUtils.getSign() CALLED');
            console.log('========================================');
            console.log('Timestamp:', timestamp);
            console.log('Path:', path);
            console.log('');

            // Get all parameters
            const gaid = AppUtils.getGAID();
            const androidId = AppUtils.getAndroidID();
            const pkgName = AppUtils.getPkna();

            console.log('GAID:', gaid);
            console.log('Android ID:', androidId);
            console.log('Package:', pkgName);

            // Call original to proceed to NRKeyManager
            const result = this.getSign(timestamp, path);

            console.log('\nGenerated Sign (first 60 chars):', result.substring(0, 60));
            console.log('========================================\n');

            return result;
        };

        console.log('[✓] Hooked AppUtils.getSign()');

    } catch (e) {
        console.log('[!] Failed to hook AppUtils.getSign():', e.message);
    }

    // Try to hook NRKeyManager directly
    try {
        // Search for NRKeyManager class
        Java.enumerateLoadedClasses({
            onMatch: function (className) {
                if (className.includes('NRKeyManager') || className.includes('KeyManager')) {
                    console.log('[?] Found class:', className);

                    try {
                        const cls = Java.use(className);
                        const methods = cls.class.getDeclaredMethods();

                        methods.forEach(function (method) {
                            console.log('   Method:', method.toString());
                        });
                    } catch (e) {
                        // Ignore
                    }
                }
            },
            onComplete: function () {
                console.log('[i] Class enumeration complete\n');
            }
        });
    } catch (e) {
        console.log('[!] Failed to enumerate classes:', e.message);
    }

    // Also hook the actual signing method to see input string
    try {
        // Find the obfuscated NRKeyManager class
        // Based on our reverse engineering, it should have a method getKey(Context, String)

        // Try common obfuscation patterns
        const possibleClasses = ['ae.b', 'com.newreading.goodreels.utils.NRKeyManager'];

        for (let i = 0; i < possibleClasses.length; i++) {
            try {
                const NRKeyManager = Java.use(possibleClasses[i]);

                // Hook getKey method
                NRKeyManager.getKey.overload('android.content.Context', 'java.lang.String').implementation = function (context, input) {
                    console.log('\n========================================');
                    console.log('[🔐] NRKeyManager.getKey() CALLED!');
                    console.log('========================================');
                    console.log('INPUT STRING:');
                    console.log(input);
                    console.log('');
                    console.log('Input Length:', input.length);
                    console.log('');

                    // Parse input to show components
                    console.log('Input breakdown:');
                    console.log('First 100 chars:', input.substring(0, 100));
                    console.log('Last 100 chars:', input.substring(input.length - 100));
                    console.log('');

                    const result = this.getKey(context, input);

                    console.log('Output Sign (first 60 chars):', result.substring(0, 60));
                    console.log('========================================\n');

                    return result;
                };

                console.log('[✓] Hooked NRKeyManager.getKey() via class:', possibleClasses[i]);
                break;

            } catch (e) {
                // Try next class
            }
        }

    } catch (e) {
        console.log('[!] Failed to hook NRKeyManager:', e.message);
    }

    console.log('\n[✅] Hooks ready!');
    console.log('[i] Now use the app (browse or play video) to trigger API calls\n');
});
