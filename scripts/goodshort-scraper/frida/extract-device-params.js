/**
 * Frida Script to Extract Device Parameters for API Sign Generation
 * 
 * Extracts:
 * - GAID (Google Advertising ID)
 * - Android Device ID
 * - APK Signature MD5
 * - User Token (after login)
 */

Java.perform(function () {
    console.log('\n[*] Starting Device Parameter Extraction...\n');

    const params = {
        gaid: null,
        androidId: null,
        appSignatureMD5: null,
        userToken: null,
        packageName: null
    };

    // Hook AppUtils.getGAID()
    try {
        const AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        AppUtils.getGAID.implementation = function () {
            const result = this.getGAID();
            params.gaid = result;
            console.log('[+] GAID:', result);
            printStatus();
            return result;
        };
        console.log('[✓] Hooked AppUtils.getGAID()');
    } catch (e) {
        console.log('[!] Failed to hook getGAID:', e.message);
    }

    // Hook AppUtils.getAndroidID()
    try {
        const AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        AppUtils.getAndroidID.implementation = function () {
            const result = this.getAndroidID();
            params.androidId = result;
            console.log('[+] Android ID:', result);
            printStatus();
            return result;
        };
        console.log('[✓] Hooked AppUtils.getAndroidID()');
    } catch (e) {
        console.log('[!] Failed to hook getAndroidID:', e.message);
    }

    // Hook d.a(Context) to get APK signature MD5
    try {
        const ClassD = Java.use('ae.d'); // Obfuscated class name

        ClassD.a.overload('android.content.Context').implementation = function (context) {
            const result = this.a(context);
            params.appSignatureMD5 = result;
            console.log('[+] APK Signature MD5:', result);
            printStatus();
            return result;
        };
        console.log('[✓] Hooked d.a(Context) for APK signature');
    } catch (e) {
        console.log('[!] Failed to hook d.a:', e.message);
    }

    // Hook SpData.getUserToken() to get user token
    try {
        const SpData = Java.use('com.newreading.goodreels.utils.SpData');

        SpData.getUserToken.implementation = function () {
            const result = this.getUserToken();
            if (result && result.length > 0) {
                params.userToken = result;
                console.log('[+] User Token:', result.substring(0, 20) + '...');
                printStatus();
            }
            return result;
        };
        console.log('[✓] Hooked SpData.getUserToken()');
    } catch (e) {
        console.log('[!] Failed to hook getUserToken:', e.message);
    }

    // Hook getPkna() to get package name
    try {
        const AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        AppUtils.getPkna.implementation = function () {
            const result = this.getPkna();
            params.packageName = result;
            console.log('[+] Package Name:', result);
            printStatus();
            return result;
        };
        console.log('[✓] Hooked AppUtils.getPkna()');
    } catch (e) {
        console.log('[!] Failed to hook getPkna:', e.message);
    }

    // Hook the actual sign generation to intercept full input
    try {
        const AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        AppUtils.getSign.implementation = function (str, str2) {
            console.log('\n[🔐] Sign Generation Called:');
            console.log('    Timestamp:', str);
            console.log('    Path:', str2);

            const result = this.getSign(str, str2);
            console.log('    Generated Sign:', result.substring(0, 40) + '...');

            return result;
        };
        console.log('[✓] Hooked AppUtils.getSign() for monitoring');
    } catch (e) {
        console.log('[!] Failed to hook getSign:', e.message);
    }

    function printStatus() {
        console.log('\n========================================');
        console.log('DEVICE PARAMETERS STATUS:');
        console.log('========================================');
        console.log('GAID:', params.gaid || '❌ Not captured yet');
        console.log('Android ID:', params.androidId || '❌ Not captured yet');
        console.log('APK Signature MD5:', params.appSignatureMD5 || '❌ Not captured yet');
        console.log('User Token:', params.userToken ? '✓ Captured' : '❌ Not captured yet (login required)');
        console.log('Package Name:', params.packageName || '❌ Not captured yet');
        console.log('========================================\n');

        // Check if we have all required params
        if (params.gaid && params.androidId && params.appSignatureMD5 && params.packageName) {
            console.log('✅ All device parameters captured!');
            if (!params.userToken) {
                console.log('⚠️  User token missing - please login in the app');
            }
            exportParams();
        }
    }

    function exportParams() {
        const exportData = {
            ...params,
            timestamp: new Date().toISOString()
        };

        console.log('\n========================================');
        console.log('EXPORT DATA (Copy this to TypeScript):');
        console.log('========================================');
        console.log(JSON.stringify(exportData, null, 2));
        console.log('========================================\n');
    }

    // RPC functions for manual extraction
    rpc.exports = {
        getParams: function () {
            return params;
        },

        printStatus: function () {
            printStatus();
        },

        export: function () {
            exportParams();
        }
    };

    console.log('\n[✓] Hooks installed! Use the app to trigger parameter capture.');
    console.log('[i] RPC functions available: getParams(), printStatus(), export()');
    console.log('[i] Parameters will be captured automatically as you use the app.\n');
});
