/**
 * Get the EXACT input string that goes into signing
 * Write to file for analysis
 */

setTimeout(function () {
    Java.perform(function () {
        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');
        var SpData = Java.use('com.newreading.goodreels.utils.SpData');
        var ActivityThread = Java.use('android.app.ActivityThread');

        var context = ActivityThread.currentApplication().getApplicationContext();

        // Collect all params
        var ts = '1769855063192';
        var path = '/home/index';
        var gaid = AppUtils.getGAID();
        var androidId = AppUtils.getAndroidID();
        var userToken = SpData.getUserToken();
        var pkna = AppUtils.getPkna();

        // Try to get MD5
        var md5 = '';
        try {
            var ae_d = Java.use('ae.d');
            md5 = ae_d.a(context);
        } catch (e) {
            send('MD5 error: ' + e.message);
        }

        // Build input as per NRKeyManager.getKey logic
        // INPUT = path + timestamp + gaid + androidId + userToken + appSignatureMD5 + packageName
        var inputStr = path + ts + gaid + androidId + userToken + md5 + pkna;

        send('=== EXACT INPUT STRING ===');
        send('Length: ' + inputStr.length);
        send('');

        // Output in parts
        send('Parts:');
        send('1. path: [' + path + ']');
        send('2. timestamp: [' + ts + ']');
        send('3. gaid: [' + gaid + ']');
        send('4. androidId: [' + androidId + ']');
        send('5. userToken length: ' + userToken.length);
        send('6. md5: [' + md5 + ']');
        send('7. pkna: [' + pkna + ']');

        send('');
        send('=== IMPORTANT: MD5 VALUE ===');
        send('MD5: ' + md5);
        send('============================');
    });
}, 3000);
