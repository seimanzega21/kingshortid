/**
 * Frida Hook Script for GoodShort v7 (Fixed)
 * Uses discovered method signatures
 */

console.log("\n[*] GoodShort Request Interceptor v7");

Java.perform(function () {

    // Hook RealInterceptorChain.proceed using Interceptor.Chain interface
    try {
        var RealInterceptorChain = Java.use("okhttp3.internal.http.RealInterceptorChain");

        // Get all overloads of proceed
        var proceedMethods = RealInterceptorChain.proceed.overloads;
        console.log("[*] Found " + proceedMethods.length + " proceed() overload(s)");

        proceedMethods.forEach(function (method) {
            method.implementation = function () {
                // Get the request using request() method from Chain interface
                try {
                    var request = this.request();
                    var requestStr = request.toString();

                    // Only log GoodShort API
                    if (requestStr.indexOf("goodreels") !== -1 || requestStr.indexOf("goodshort") !== -1) {
                        console.log("\n" + "=".repeat(70));
                        console.log("[REQUEST]");
                        console.log(requestStr);
                        console.log("=".repeat(70) + "\n");
                    }
                } catch (e) {
                    // Silently ignore errors
                }

                // Call original method based on arguments
                if (arguments.length === 0) {
                    return this.proceed();
                } else {
                    return this.proceed(arguments[0]);
                }
            };
        });

        console.log("[+] Hooked RealInterceptorChain.proceed()");

    } catch (e) {
        console.log("[-] RealInterceptorChain hook failed: " + e);
    }

    // Also hook HttpLoggingInterceptor.intercept as backup
    try {
        var HttpLoggingInterceptor = Java.use("okhttp3.logging.HttpLoggingInterceptor");

        HttpLoggingInterceptor.intercept.implementation = function (chain) {
            try {
                var request = chain.request();
                var requestStr = request.toString();

                if (requestStr.indexOf("goodreels") !== -1) {
                    console.log("[LOG INTERCEPTOR] " + requestStr);
                }
            } catch (e) { }

            return this.intercept(chain);
        };

        console.log("[+] Hooked HttpLoggingInterceptor.intercept()");
    } catch (e) {
        console.log("[-] HttpLoggingInterceptor hook failed: " + e);
    }

    console.log("\n[*] Ready! Browse GoodShort to capture requests...\n");
});
