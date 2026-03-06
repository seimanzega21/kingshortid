/**
 * Get FULL userToken and all parameters
 */

setTimeout(function () {
    Java.perform(function () {
        send('=== FULL PARAMETER EXTRACTION ===');

        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');
        var SpData = Java.use('com.newreading.goodreels.utils.SpData');

        // Get all parameters
        var gaid = AppUtils.getGAID();
        var androidId = AppUtils.getAndroidID();
        var pkna = AppUtils.getPkna();
        var userToken = SpData.getUserToken();

        send('GAID: ' + gaid);
        send('AndroidID: ' + androidId);
        send('Package: ' + pkna);
        send('UserToken: ' + userToken);
        send('UserToken length: ' + (userToken ? userToken.length : 0));

        // Try to get appSignatureMD5 from ae.d or wherever
        try {
            // The d.a method takes Context and returns MD5
            var d_class = Java.use('ae.d');

            // Get application context
            var ActivityThread = Java.use('android.app.ActivityThread');
            var context = ActivityThread.currentApplication().getApplicationContext();

            // Try calling the method
            var md5 = d_class.a(context);
            send('AppSignatureMD5 (ae.d.a): ' + md5);
        } catch (e) {
            send('ae.d.a error: ' + e.message);
        }

        // Now generate sign and compare
        var ts = '1769855063192';
        var path = '/home/index';
        var sign = AppUtils.getSign(ts, path);

        send('');
        send('Generated sign (length ' + sign.length + '):');
        send(sign);

        // Build our expected input string
        send('');
        send('Expected input string components:');
        send('path: ' + path);
        send('timestamp: ' + ts);
        send('gaid: ' + gaid);
        send('androidId: ' + androidId);
        send('userToken: ' + userToken);
        send('pkna: ' + pkna);

        send('=================================');
    });
}, 3000);
