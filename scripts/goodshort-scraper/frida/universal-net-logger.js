/**
 * Universal Network Traffic Logger
 * Hooks at lower level to capture ALL HTTP traffic
 */

Java.perform(function () {
    console.log('\n[*] Universal Network Logger v4\n');

    // Approach 1: Hook at URL connection level
    try {
        const URL = Java.use('java.net.URL');
        URL.openConnection.overload().implementation = function () {
            console.log('[NET] URL.openConnection:', this.toString());
            return this.openConnection();
        };
        console.log('[✓] java.net.URL.openConnection hooked');
    } catch (e) {
        console.log('[!] URL hook failed:', e.message);
    }

    // Approach 2: Hook HttpURLConnection
    try {
        const HttpURLConnection = Java.use('java.net.HttpURLConnection');
        HttpURLConnection.setRequestProperty.implementation = function (key, value) {
            if (key === 'sign' || key === 'timestamp' || key === 'deviceId' ||
                key === 'androidId' || key === 'Authorization') {
                console.log('[HEADER] ' + key + ': ' + value);
            }
            return this.setRequestProperty(key, value);
        };
        console.log('[✓] HttpURLConnection.setRequestProperty hooked');
    } catch (e) {
        console.log('[!] HttpURLConnection hook failed:', e.message);
    }

    // Approach 3: Hook okhttp3 Request.Builder if exists
    try {
        const RequestBuilder = Java.use('okhttp3.Request$Builder');

        RequestBuilder.addHeader.implementation = function (name, value) {
            if (name === 'sign') {
                console.log('\n========================================');
                console.log('[🔐] OkHttp SIGN HEADER CAPTURED!');
                console.log('========================================');
                console.log('Sign:', value);
                console.log('========================================\n');
            } else if (name === 'timestamp' || name === 'deviceId' || name === 'androidId') {
                console.log('[HEADER] ' + name + ': ' + value);
            }
            return this.addHeader(name, value);
        };

        RequestBuilder.header.implementation = function (name, value) {
            if (name === 'sign') {
                console.log('\n========================================');
                console.log('[🔐] OkHttp SIGN HEADER CAPTURED!');
                console.log('========================================');
                console.log('Sign:', value);
                console.log('========================================\n');
            }
            return this.header(name, value);
        };

        console.log('[✓] okhttp3.Request$Builder hooked');
    } catch (e) {
        console.log('[!] okhttp3 hook failed:', e.message);
    }

    // Approach 4: Hook Retrofit if used
    try {
        const OkHttpClient = Java.use('okhttp3.OkHttpClient');
        OkHttpClient.newCall.implementation = function (request) {
            console.log('\n[📡] OkHttp Request:');
            console.log('  URL:', request.url().toString());
            console.log('  Method:', request.method());

            // Try to get sign header
            const headers = request.headers();
            const sign = headers.get('sign');
            if (sign) {
                console.log('\n  🔐 SIGN:', sign);
            }

            return this.newCall(request);
        };
        console.log('[✓] okhttp3.OkHttpClient.newCall hooked');
    } catch (e) {
        console.log('[!] OkHttpClient hook failed:', e.message);
    }

    // Approach 5: Just log ALL public method calls on AppUtils
    try {
        const AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        // Log when getSign is called
        AppUtils.getSign.implementation = function (arg1, arg2) {
            console.log('\n========================================');
            console.log('[📝] AppUtils.getSign CALLED!');
            console.log('========================================');
            console.log('Arg1:', arg1);
            console.log('Arg2:', arg2);

            const result = this.getSign(arg1, arg2);
            console.log('\nResult:', result);
            console.log('========================================\n');
            return result;
        };

        console.log('[✓] AppUtils.getSign hooked');
    } catch (e) {
        console.log('[!] AppUtils hook failed:', e.message);
    }

    console.log('\n[✅] All hooks ready! Now interact with the app...\n');
    console.log('[i] If you see this but no output, try:');
    console.log('    1. Close app completely');
    console.log('    2. Re-run this script with -f flag');
    console.log('    3. Wait for app to load then browse\n');
});
