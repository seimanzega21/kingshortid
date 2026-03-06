/**
 * Universal Hook - Capture ALL API sign generation calls
 * Works by hooking AppUtils methods we know exist
 */

Java.perform(function () {
    console.log('\n[*] Universal Sign Extraction Hook Starting...\n');

    // Hook AppUtils.getSign() - This we know works!
    try {
        const AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        // Hook getSign to see complete input
        const getSign = AppUtils.getSign.overload('java.lang.String', 'java.lang.String');
        getSign.implementation = function (timestamp, path) {
            console.log('\n========================================');
            console.log('[🔐] getSign() Called!');
            console.log('========================================');
            console.log('Timestamp:', timestamp);
            console.log('Path:', path);

            // Call getGAID, getAndroidID manually to see values
            const gaid = AppUtils.getGAID();
            const androidId = AppUtils.getAndroidID();
            const pkgName = AppUtils.getPkna();

            console.log('GAID:', gaid);
            console.log('Android ID:', androidId);
            console.log('Package:', pkgName);

            // Get user token
            try {
                const SpData = Java.use('com.newreading.goodreels.utils.SpData');
                const userToken = SpData.getUserToken();
                console.log('User Token:', userToken ? userToken.substring(0, 30) + '...' : 'EMPTY');
            } catch (e) {
                console.log('User Token: (unable to get)');
            }

            // Now call original to get signature MD5 appended
            const result = this.getSign(timestamp, path);

            console.log('\n📝 Complete Input Pattern:');
            console.log('   path + timestamp + gaid + androidId + userToken + [APK_SIG_MD5] + packageName');
            console.log('\n🔑 Generated Sign:', result.substring(0, 60) + '...');
            console.log('========================================\n');

            return result;
        };

        console.log('[✓] Hooked AppUtils.getSign()');
        console.log('[i] Now browse or play a video to trigger!\n');

    } catch (e) {
        console.log('[!] Failed to hook getSign:', e.message, '\n');
    }

    // Hook getH5HeaderData to see final headers
    try {
        const AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        const getH5HeaderData = AppUtils.getH5HeaderData.overload('java.lang.String', 'java.lang.String');
        getH5HeaderData.implementation = function (timestamp, path) {
            console.log('\n[📤] getH5HeaderData() called for:', path);
            const result = this.getH5HeaderData(timestamp, path);
            console.log('[📤] Header:', result.substring(0, 100) + '...\n');
            return result;
        };

        console.log('[✓] Hooked AppUtils.getH5HeaderData()\n');

    } catch (e) {
        console.log('[!] Failed to hook getH5HeaderData:', e.message, '\n');
    }

    console.log('[✅] Hooks ready! Browse the app or play a video.\n');
});
