/**
 * Hook NRKeyManager getKey to see EXACT input string
 */

setTimeout(function () {
    Java.perform(function () {
        send('=== Hooking Sign Generation Flow ===');

        // First find the actual key manager class
        // Based on decompiled code, it might be ae.b or similar

        try {
            // Hook AppUtils.getSign to trace the call
            var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

            AppUtils.getSign.implementation = function (timestamp, path) {
                send('');
                send('=== AppUtils.getSign called ===');
                send('timestamp: ' + timestamp);
                send('path: ' + path);

                // Get all internal params
                var gaid = AppUtils.getGAID.call(this);
                var androidId = AppUtils.getAndroidID.call(this);
                var pkna = AppUtils.getPkna.call(this);

                var SpData = Java.use('com.newreading.goodreels.utils.SpData');
                var userToken = SpData.getUserToken();

                // Try to get appSignatureMD5
                var ActivityThread = Java.use('android.app.ActivityThread');
                var context = ActivityThread.currentApplication().getApplicationContext();

                // Try ae.d.a(context) for MD5
                var md5 = '';
                try {
                    var ae_d = Java.use('ae.d');
                    md5 = ae_d.a(context);
                } catch (e) {
                    send('ae.d.a failed: ' + e.message);
                }

                send('gaid: ' + gaid);
                send('androidId: ' + androidId);
                send('userToken: ' + userToken);
                send('appSignatureMD5: ' + md5);
                send('pkna: ' + pkna);

                // Build expected input
                var expectedInput = path + timestamp + gaid + androidId + userToken + md5 + pkna;
                send('');
                send('Expected input string:');
                send(expectedInput);
                send('Input length: ' + expectedInput.length);

                // Call original
                var result = this.getSign(timestamp, path);
                send('');
                send('Result sign: ' + result);
                send('===========================');

                return result;
            };

            send('[✓] AppUtils.getSign hooked');

            // Now trigger a call
            send('');
            send('Triggering test call...');
            var testSign = AppUtils.getSign('1769855063192', '/home/index');
            send('Test complete');

        } catch (e) {
            send('[!] Error: ' + e.message);
            send(e.stack);
        }
    });
}, 3000);
