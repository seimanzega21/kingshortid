/**
 * Specifically target GoodReels API calls
 */

Java.perform(function () {
    console.log('\n[*] GoodReels API Logger v5\n');

    // Hook URL.openConnection and filter for goodreels API
    try {
        const URL = Java.use('java.net.URL');
        URL.openConnection.overload().implementation = function () {
            const url = this.toString();

            // Only log goodreels API calls
            if (url.includes('goodreels.com') || url.includes('api-akm')) {
                console.log('\n========================================');
                console.log('[🎯] GOODREELS API DETECTED!');
                console.log('========================================');
                console.log('URL:', url);
                console.log('========================================\n');
            }

            return this.openConnection();
        };
        console.log('[✓] URL filter for goodreels.com active');
    } catch (e) {
        console.log('[!] URL hook failed:', e.message);
    }

    // Hook HttpURLConnection to get headers for goodreels calls
    try {
        const HttpURLConnection = Java.use('java.net.HttpURLConnection');

        // Store URLs being accessed
        let currentUrl = '';

        HttpURLConnection.getURL.implementation = function () {
            const url = this.getURL();
            currentUrl = url ? url.toString() : '';
            return url;
        };

        HttpURLConnection.setRequestProperty.implementation = function (key, value) {
            // Only log for goodreels API
            if (currentUrl.includes('goodreels') || currentUrl.includes('api-akm')) {
                console.log('[HEADER] ' + key + ': ' + value);

                if (key === 'sign') {
                    console.log('\n🔐🔐🔐 SIGN CAPTURED! 🔐🔐🔐');
                    console.log('Value:', value);
                    console.log('🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐\n');
                }
            }
            return this.setRequestProperty(key, value);
        };

        console.log('[✓] HttpURLConnection filter active');
    } catch (e) {
        console.log('[!] HttpURLConnection hook failed:', e.message);
    }

    // AppUtils - this should work regardless of OkHttp
    try {
        const AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        AppUtils.getSign.implementation = function (timestamp, path) {
            console.log('\n========================================');
            console.log('[📝] AppUtils.getSign() TRIGGERED!');
            console.log('========================================');
            console.log('timestamp:', timestamp);
            console.log('path:', path);

            const result = this.getSign(timestamp, path);

            console.log('\nGenerated sign:', result);
            console.log('========================================\n');

            return result;
        };

        console.log('[✓] AppUtils.getSign hooked');

        // Also hook getH5HeaderData
        AppUtils.getH5HeaderData.implementation = function (timestamp, path) {
            console.log('\n========================================');
            console.log('[🔐] AppUtils.getH5HeaderData() TRIGGERED!');
            console.log('========================================');
            console.log('timestamp:', timestamp);
            console.log('path:', path);

            const result = this.getH5HeaderData(timestamp, path);
            console.log('Result:', result);
            console.log('========================================\n');

            return result;
        };

        console.log('[✓] AppUtils.getH5HeaderData hooked');

    } catch (e) {
        console.log('[!] AppUtils hook failed:', e.message);
    }

    console.log('\n[✅] Filters ready - waiting for goodreels.com API calls...\n');
});
