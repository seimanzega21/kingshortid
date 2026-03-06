/**
 * Hook AppUtils.getSign AND getH5HeaderData to capture EXACT parameters
 */

Java.perform(function () {
    console.log('\n[*] Sign Capture - Deep Hook v3\n');

    try {
        const AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        // Hook getSign (1 overload as confirmed)
        AppUtils.getSign.implementation = function (timestamp, path) {
            console.log('\n========================================');
            console.log('[📝] AppUtils.getSign() CALLED!');
            console.log('========================================');
            console.log('Timestamp:', timestamp);
            console.log('Path:', path);

            // Get all parameters that go into signing
            const gaid = AppUtils.getGAID.call(this);
            const androidId = AppUtils.getAndroidID.call(this);
            const pkna = AppUtils.getPkna.call(this);

            console.log('\nDevice params:');
            console.log('  GAID:', gaid);
            console.log('  AndroidID:', androidId);
            console.log('  PackageName:', pkna);

            const result = this.getSign(timestamp, path);

            console.log('\nGenerated Sign:');
            console.log(result);
            console.log('========================================\n');

            return result;
        };

        console.log('[✓] AppUtils.getSign hooked');

        // Also hook getH5HeaderData to see all headers
        if (AppUtils.getH5HeaderData) {
            const getH5Overloads = AppUtils.getH5HeaderData.overloads;
            console.log('[i] getH5HeaderData overloads:', getH5Overloads.length);

            getH5Overloads.forEach(function (overload, idx) {
                overload.implementation = function () {
                    console.log('\n========================================');
                    console.log('[🔐] AppUtils.getH5HeaderData() - overload ' + idx);
                    console.log('========================================');
                    console.log('Arguments:', arguments.length);

                    for (let i = 0; i < arguments.length; i++) {
                        const arg = arguments[i];
                        if (arg !== null && arg !== undefined) {
                            console.log('  Arg[' + i + ']:', String(arg));
                        } else {
                            console.log('  Arg[' + i + ']: null/undefined');
                        }
                    }

                    const result = this.getH5HeaderData.apply(this, arguments);

                    // Result is a Map, iterate and print
                    console.log('\nResult (headers):');
                    try {
                        const Map = Java.use('java.util.Map');
                        const Set = Java.use('java.util.Set');
                        const Iterator = Java.use('java.util.Iterator');

                        const entrySet = result.entrySet();
                        const iterator = entrySet.iterator();

                        while (iterator.hasNext()) {
                            const entry = iterator.next();
                            const key = entry.getKey();
                            const value = entry.getValue();
                            console.log('  ' + key + ': ' + value);
                        }
                    } catch (e) {
                        console.log('  [Could not iterate result:', e.message + ']');
                        console.log('  Raw:', result);
                    }

                    console.log('========================================\n');

                    return result;
                };
            });

            console.log('[✓] AppUtils.getH5HeaderData hooked');
        }

    } catch (e) {
        console.log('[!] Failed:', e.message);
    }

    console.log('\n[✅] Ready! Browse the app to trigger API calls...\n');
});
