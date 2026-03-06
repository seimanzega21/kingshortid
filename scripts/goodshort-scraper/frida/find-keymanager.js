/**
 * Hook NRKeyManager.getKey to capture the EXACT input string
 */

setTimeout(function () {
    Java.perform(function () {
        send('=== Searching for NRKeyManager ===');

        // Find classes containing "Key"
        Java.enumerateLoadedClasses({
            onMatch: function (className) {
                if (className.includes('NRKey') ||
                    (className.includes('ae.') && className.length < 10)) {
                    send('Found: ' + className);
                }
            },
            onComplete: function () {
                send('Search complete');
            }
        });

        // Try to hook ae.d class (obfuscated NRKeyManager)
        try {
            var ae_d = Java.use('ae.d');
            send('ae.d found! Methods:');
            var methods = ae_d.class.getDeclaredMethods();
            methods.forEach(function (m) {
                send('  - ' + m.getName() + ': ' + m.toString());
            });
        } catch (e) {
            send('ae.d not found: ' + e.message);
        }

        // Try ae.b
        try {
            var ae_b = Java.use('ae.b');
            send('ae.b found! Methods:');
            var methods = ae_b.class.getDeclaredMethods();
            methods.forEach(function (m) {
                send('  - ' + m.getName() + ': ' + m.toString());
            });
        } catch (e) {
            send('ae.b not found: ' + e.message);
        }

        // Try to call getSign and get input
        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        // Get SpData to see userToken
        try {
            var SpData = Java.use('com.newreading.goodreels.utils.SpData');
            send('SpData.getUserToken: ' + SpData.getUserToken());
        } catch (e) {
            send('SpData.getUserToken error: ' + e.message);
        }

        // Check d.a for APK signature MD5
        try {
            var d_class = Java.use('ae.d');
            // Look for method that returns MD5
            send('Checking ae.d methods...');
        } catch (e) {
            send('ae.d check error: ' + e.message);
        }
    });
}, 3000);
