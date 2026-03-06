"""
Frida Hook to Extract GoodShort API Signing Mechanism
Will intercept sign header generation and log the algorithm / keys
"""

Java.perform(function () {
    console.log("[*] Starting GoodShort Signature Hook");
    console.log("[*] Target: API request signing mechanism");

    // Hook OkHttp Interceptor (most apps use this for adding headers)
    try {
        var Interceptor = Java.use("okhttp3.Interceptor");
        console.log("[+] Found OkHttp Interceptor");
    } catch (e) {
        console.log("[-] OkHttp not found, trying alternative...");
    }

    // Hook common signing classes
    var signClassNames = [
        "com.goodshort.sign.SignUtil",
        "com.goodshort.utils.SignUtil",
        "com.goodshort.network.SignUtil",
        "com.goodreels.sign.SignUtil",
        "com.goodreels.utils.SignUtil"
    ];

    signClassNames.forEach(function (className) {
        try {
            var SignUtil = Java.use(className);
            console.log("[+] Found signing class: " + className);

            // Hook all methods
            var methods = SignUtil.class.getDeclaredMethods();
            methods.forEach(function (method) {
                var methodName = method.getName();
                console.log("[*] Method found: " + methodName);

                try {
                    SignUtil[methodName].overload().implementation = function () {
                        console.log("[HOOK] " + className + "." + methodName + " called");
                        console.log("  Arguments: " + JSON.stringify(arguments));

                        var result = this[methodName].apply(this, arguments);

                        console.log("  Result (sign): " + result);
                        console.log("  Result type: " + (typeof result));

                        return result;
                    };
                } catch (e2) {
                    // Method might have different overloads
                }
            });
        } catch (e) {
            // Class not found
        }
    });

    // Hook Request.Builder to intercept when headers are added
    try {
        var RequestBuilder = Java.use("okhttp3.Request$Builder");

        RequestBuilder.addHeader.implementation = function (name, value) {
            if (name === "sign" || name === "Sign") {
                console.log("\n[SIGN HEADER FOUND]");
                console.log("  Header name: " + name);
                console.log("  Sign value: " + value);

                // Try to get the request URL
                try {
                    var currentRequest = this.build();
                    var url = currentRequest.url().toString();
                    console.log("  Request URL: " + url);
                } catch (e) { }

                console.log("");
            }

            return this.addHeader(name, value);
        };

        console.log("[+] Hooked Request.Builder.addHeader");
    } catch (e) {
        console.log("[-] Could not hook Request.Builder: " + e);
    }

    // Hook crypto functions (RSA, SHA256)
    try {
        var MessageDigest = Java.use("java.security.MessageDigest");
        MessageDigest.digest.overload('[B').implementation = function (input) {
            var result = this.digest(input);

            var algorithm = this.getAlgorithm();
            if (algorithm.indexOf("SHA") >= 0) {
                console.log("[CRYPTO] MessageDigest." + algorithm);
                console.log("  Input: " + Java.use("java.lang.String").$new(input));
                console.log("  Output (hex): " + bytesToHex(result));
            }

            return result;
        };

        console.log("[+] Hooked MessageDigest.digest");
    } catch (e) {
        console.log("[-] Could not hook MessageDigest: " + e);
    }

    // Hook Signature class (for RSA signing)
    try {
        var Signature = Java.use("java.security.Signature");

        Signature.sign.overload().implementation = function () {
            var algorithm = this.getAlgorithm();
            console.log("[RSA SIGN]");
            console.log("  Algorithm: " + algorithm);

            var result = this.sign();
            console.log("  Signature (base64): " + Java.use("android.util.Base64").encodeToString(result, 0));

            return result;
        };

        console.log("[+] Hooked Signature.sign");
    } catch (e) {
        console.log("[-] Could not hook Signature: " + e);
    }

    console.log("\n[*] All hooks installed. Waiting for API calls...\n");
});

function bytesToHex(bytes) {
    var hex = [];
    for (var i = 0; i < bytes.length; i++) {
        hex.push(("0" + (bytes[i] & 0xFF).toString(16)).slice(-2));
    }
    return hex.join("");
}
