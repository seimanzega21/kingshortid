/**
 * Hook OkHttp/HttpURLConnection to capture actual request details
 */

Java.perform(function () {
    console.log('\n[*] HTTP Request Logger - v2\n');

    // Hook OkHttp3
    try {
        const OkHttpClient$Builder = Java.use('okhttp3.OkHttpClient$Builder');
        const OkHttpClient = Java.use('okhttp3.OkHttpClient');
        const Request = Java.use('okhttp3.Request');
        const RequestBody = Java.use('okhttp3.RequestBody');
        const Headers = Java.use('okhttp3.Headers');

        // Hook newCall to intercept requests
        OkHttpClient.newCall.overload('okhttp3.Request').implementation = function (request) {
            console.log('\n========================================');
            console.log('[📡] HTTP REQUEST INTERCEPTED');
            console.log('========================================');

            const url = request.url().toString();
            console.log('URL:', url);
            console.log('Method:', request.method());

            // Get headers
            const headers = request.headers();
            const headerCount = headers.size();
            console.log('\nHeaders (' + headerCount + ' total):');

            for (let i = 0; i < headerCount; i++) {
                const name = headers.name(i);
                const value = headers.value(i);

                // Log important headers
                if (name === 'sign' || name === 'timestamp' || name === 'deviceId' ||
                    name === 'androidId' || name === 'Authorization') {
                    console.log('  [*] ' + name + ': ' + value);
                }
            }

            // Check for sign header specifically
            const signValue = headers.get('sign');
            if (signValue) {
                console.log('\n🔐 SIGN HEADER FOUND:');
                console.log(signValue);
            }

            console.log('========================================\n');

            return this.newCall(request);
        };

        console.log('[✓] OkHttp3 intercepted');

    } catch (e) {
        console.log('[!] Failed to hook OkHttp3:', e.message);
    }

    // Also try to hook the utility class directly
    try {
        const AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        // Find all methods
        const methods = AppUtils.class.getDeclaredMethods();
        console.log('\n[i] AppUtils Methods:');
        methods.forEach(function (method) {
            console.log('  - ' + method.getName());
        });

        // Hook getSign with all possible overloads
        const getSignOverloads = AppUtils.getSign.overloads;
        console.log('\n[i] getSign overloads:', getSignOverloads.length);

        getSignOverloads.forEach(function (overload, idx) {
            overload.implementation = function () {
                console.log('\n========================================');
                console.log('[📝] AppUtils.getSign() - overload ' + idx);
                console.log('========================================');
                console.log('Arguments:', arguments.length);

                for (let i = 0; i < arguments.length; i++) {
                    console.log('  Arg[' + i + ']:', arguments[i]);
                }

                const result = this.getSign.apply(this, arguments);
                console.log('\nResult (first 60):', result.substring(0, 60));
                console.log('========================================\n');

                return result;
            };
        });

        console.log('[✓] AppUtils.getSign hooked');

    } catch (e) {
        console.log('[!] Failed to hook AppUtils:', e.message);
    }

    console.log('\n[✅] Ready! Browse the app to trigger API calls...\n');
});
