/**
 * Simplified API Logger - Stable Version
 */

console.log("\n" + "=".repeat(70));
console.log("[*] GoodShort API Logger - STABLE MODE");
console.log("=".repeat(70) + "\n");

var capturedRequests = [];

Java.perform(function () {
    console.log("[+] Starting hooks...\n");

    var RealInterceptorChain = Java.use("okhttp3.internal.http.RealInterceptorChain");

    var proceed = RealInterceptorChain.proceed.overload();

    proceed.implementation = function () {
        var request = this.request();
        var url = request.url().toString();
        var response = this.proceed();

        // Only log API calls
        if (url.indexOf("api-akm.goodreels.com") !== -1) {
            try {
                var method = request.method();
                var headers = request.headers();

                console.log("\n" + "─".repeat(70));
                console.log("🌐 API CALL");
                console.log("─".repeat(70));
                console.log("URL: " + url);
                console.log("Method: " + method);

                // Log important headers
                var sign = headers.get("sign");
                var timestamp = headers.get("timestamp");
                var userAgent = headers.get("user-agent");

                if (sign) console.log("Sign: " + sign);
                if (timestamp) console.log("Timestamp: " + timestamp);
                if (userAgent) console.log("User-Agent: " + userAgent);

                // Store simplified data
                capturedRequests.push({
                    url: url,
                    method: method,
                    sign: sign,
                    timestamp: timestamp,
                    time: new Date().toISOString()
                });

                console.log("Total captured: " + capturedRequests.length);
                console.log("─".repeat(70) + "\n");

            } catch (e) {
                // Ignore errors
            }
        }

        return response;
    };

    console.log("[✓] Hook installed!");
    console.log("\n📱 Browse dramas in the app now\n");
    console.log("Commands:");
    console.log("  status()  - Show count");
    console.log("  export()  - Show all data\n");
});

rpc.exports = {
    status: function () {
        console.log("\n📊 Captured: " + capturedRequests.length + " requests\n");
        return capturedRequests.length;
    },

    export: function () {
        console.log("\n" + "=".repeat(70));
        console.log("CAPTURED DATA");
        console.log("=".repeat(70));
        console.log(JSON.stringify(capturedRequests, null, 2));
        console.log("=".repeat(70) + "\n");
        return capturedRequests;
    }
};
