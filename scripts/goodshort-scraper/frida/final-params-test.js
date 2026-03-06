/**
 * FINAL TEST - Get all params and input string, write to console clearly
 */

setTimeout(function () {
    Java.perform(function () {
        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');
        var SpData = Java.use('com.newreading.goodreels.utils.SpData');

        // Get all params
        var ts = '1769855063192';
        var path = '/home/index';
        var gaid = AppUtils.getGAID();
        var androidId = AppUtils.getAndroidID();
        var userToken = SpData.getUserToken();
        var pkna = AppUtils.getPkna();

        console.log('');
        console.log('============= PARAMS ==============');
        console.log('path=' + path);
        console.log('timestamp=' + ts);
        console.log('gaid=' + gaid);
        console.log('androidId=' + androidId);
        console.log('userToken=' + userToken);
        console.log('pkna=' + pkna);
        console.log('');

        // Build input - this is our assumed order
        var input = path + ts + gaid + androidId + userToken + '' + pkna;
        console.log('============= INPUT ===============');
        console.log('input_length=' + input.length);
        console.log('input=' + input);
        console.log('');

        // Get the actual sign from app
        var appSign = AppUtils.getSign(ts, path);
        console.log('============= SIGN ================');
        console.log('app_sign=' + appSign);
        console.log('===================================');
    });
}, 3000);
