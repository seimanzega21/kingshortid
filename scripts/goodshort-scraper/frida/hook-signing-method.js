/**
 * Find and hook the ACTUAL signing function (ae.b.b or similar)
 */

setTimeout(function () {
    Java.perform(function () {
        send('=== Finding RSA Signing Method ===');

        // List all ae package classes  
        Java.enumerateLoadedClasses({
            onMatch: function (className) {
                if (className.startsWith('ae.')) {
                    try {
                        var cls = Java.use(className);
                        var methods = cls.class.getDeclaredMethods();
                        if (methods.length > 0) {
                            send('Class: ' + className);
                            methods.forEach(function (m) {
                                if (m.toString().includes('String') && m.toString().includes('byte')) {
                                    send('  Method: ' + m.getName() + ' -> ' + m.toString().substring(0, 100));
                                }
                            });
                        }
                    } catch (e) { }
                }
            },
            onComplete: function () {
                send('Class enumeration complete');
            }
        });

        // Try to hook ae.b.b (likely the signing method)
        try {
            var ae_b = Java.use('ae.b');
            send('');
            send('ae.b methods:');
            var methods = ae_b.class.getDeclaredMethods();
            methods.forEach(function (m) {
                send('  ' + m.toString());
            });

            // Hook the b method if it takes a String
            ae_b.b.overloads.forEach(function (overload, idx) {
                send('Hooking ae.b.b overload ' + idx);
                overload.implementation = function () {
                    send('');
                    send('=== ae.b.b called ===');
                    for (var i = 0; i < arguments.length; i++) {
                        var arg = arguments[i];
                        if (typeof arg === 'string') {
                            send('Arg[' + i + '] (STRING, len=' + arg.length + '):');
                            // Print first 200 chars
                            send(arg.substring(0, Math.min(200, arg.length)));
                            if (arg.length > 200) {
                                send('... (truncated)');
                            }
                        } else {
                            send('Arg[' + i + '] (' + typeof arg + '): ' + arg);
                        }
                    }

                    var result = overload.apply(this, arguments);
                    send('Result type: ' + typeof result);
                    if (typeof result === 'string') {
                        send('Result: ' + result);
                    }
                    send('=====================');
                    return result;
                };
            });

            send('ae.b.b hooked!');
        } catch (e) {
            send('ae.b error: ' + e.message);
        }

        // Now trigger by calling AppUtils.getSign
        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');
        send('');
        send('Triggering getSign...');
        var sign = AppUtils.getSign('1769855063192', '/home/index');
        send('getSign returned');
    });
}, 3000);
