/**
 * Extract COMPLETE userToken and test sign
 */

setTimeout(function () {
    Java.perform(function () {
        var SpData = Java.use('com.newreading.goodreels.utils.SpData');
        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        // Get full userToken
        var userToken = SpData.getUserToken();

        // Print character by character to avoid truncation
        send('UserToken full (length ' + userToken.length + '):');

        // Split into chunks
        var chunkSize = 80;
        for (var i = 0; i < userToken.length; i += chunkSize) {
            send(userToken.substring(i, Math.min(i + chunkSize, userToken.length)));
        }

        send('');
        send('Other params:');
        send('GAID: ' + AppUtils.getGAID());
        send('AndroidID: ' + AppUtils.getAndroidID());
        send('Package: ' + AppUtils.getPkna());

        // Generate sign
        send('');
        send('Sign generated:');
        var sign = AppUtils.getSign('1769855063192', '/home/index');

        // Split sign into chunks too
        for (var i = 0; i < sign.length; i += chunkSize) {
            send(sign.substring(i, Math.min(i + chunkSize, sign.length)));
        }

        send('');
        send('DONE');
    });
}, 3000);
