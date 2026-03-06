/**
 * GoodShort Complete API Logger
 * Captures ALL network traffic for reverse engineering
 */

console.log("\n" + "=".repeat(70));
console.log("[*] GoodShort API Logger - COMPLETE CAPTURE MODE");
console.log("=".repeat(70) + "\n");

var capturedRequests = [];
var requestCounter = 0;

// Helper: Convert bytes to readable string
function bytesToString(bytes) {
    try {
        return Java.use("java.lang.String").$new(bytes);
    } catch (e) {
        return "[Binary Data]";
    }
}

// Helper: Format headers
function formatHeaders(headers) {
    var result = {};
    if (!headers) return result;

    var names = headers.names();
    var nameIterator = names.iterator();

    while (nameIterator.hasNext()) {
        var name = nameIterator.next();
        result[name] = headers.get(name);
    }

    return result;
}

Java.perform(function () {
    console.log("[+] Hooking OkHttp3...\n");

    var RealInterceptorChain = Java.use("okhttp3.internal.http.RealInterceptorChain");
    var Response = Java.use("okhttp3.Response");
    var ResponseBody = Java.use("okhttp3.ResponseBody");

    RealInterceptorChain.proceed.overloads.forEach(function (method) {
        method.implementation = function () {
            var request = this.request();
            var url = request.url().toString();
            var method = request.method();
            var response = null;

            // Call original
            if (arguments.length === 0) {
                response = this.proceed();
            } else {
                response = this.proceed(arguments[0]);
            }

            // ========== CAPTURE API REQUESTS ==========
            if (url.indexOf("api-akm.goodreels.com") !== -1 ||
                url.indexOf("hwyclientreels") !== -1) {

                requestCounter++;
                var requestData = {
                    id: requestCounter,
                    timestamp: new Date().toISOString(),
                    method: method,
                    url: url,
                    requestHeaders: {},
                    requestBody: null,
                    responseHeaders: {},
                    responseBody: null,
                    statusCode: response.code()
                };

                // === REQUEST HEADERS ===
                var reqHeaders = request.headers();
                requestData.requestHeaders = formatHeaders(reqHeaders);

                // === REQUEST BODY ===
                try {
                    var reqBody = request.body();
                    if (reqBody) {
                        var buffer = Java.use("okio.Buffer").$new();
                        reqBody.writeTo(buffer);
                        requestData.requestBody = buffer.readUtf8();
                    }
                } catch (e) {
                    requestData.requestBody = "[Error reading request body]";
                }

                // === RESPONSE HEADERS ===
                var respHeaders = response.headers();
                requestData.responseHeaders = formatHeaders(respHeaders);

                // === RESPONSE BODY ===
                try {
                    var responseBody = response.body();
                    var bodyString = responseBody.string();
                    requestData.responseBody = bodyString;

                    // Re-create response body (consumed)
                    var mediaType = responseBody.contentType();
                    var newBody = ResponseBody.create(mediaType, bodyString);
                    response = response.newBuilder().body(newBody).build();
                } catch (e) {
                    requestData.responseBody = "[Error reading response body]";
                }

                // Store
                capturedRequests.push(requestData);

                // === PRINT IMPORTANT DETAILS ===
                console.log("\n" + "─".repeat(70));
                console.log("🌐 API REQUEST #" + requestCounter);
                console.log("─".repeat(70));
                console.log("📍 URL: " + url);
                console.log("🔧 Method: " + method);
                console.log("📊 Status: " + response.code());

                // Print critical headers
                if (requestData.requestHeaders.sign) {
                    console.log("🔐 Sign: " + requestData.requestHeaders.sign);
                }
                if (requestData.requestHeaders.timestamp) {
                    console.log("⏰ Timestamp: " + requestData.requestHeaders.timestamp);
                }
                if (requestData.requestHeaders["user-agent"]) {
                    console.log("🤖 User-Agent: " + requestData.requestHeaders["user-agent"]);
                }
                if (requestData.requestHeaders.authorization || requestData.requestHeaders.token) {
                    console.log("🎫 Auth: " + (requestData.requestHeaders.authorization || requestData.requestHeaders.token));
                }

                // Print body preview
                if (requestData.requestBody && requestData.requestBody !== "[Error reading request body]") {
                    console.log("📤 Request Body: " + requestData.requestBody.substring(0, 200));
                }

                if (requestData.responseBody && requestData.responseBody !== "[Error reading response body]") {
                    var preview = requestData.responseBody.substring(0, 300);
                    console.log("📥 Response Preview: " + preview);

                    // Try to parse as JSON and show structure
                    try {
                        var json = JSON.parse(requestData.responseBody);
                        if (json.data) {
                            console.log("📦 Response has 'data' field");
                            if (Array.isArray(json.data)) {
                                console.log("   📋 Data is array with " + json.data.length + " items");
                            } else if (typeof json.data === 'object') {
                                var keys = Object.keys(json.data);
                                console.log("   🔑 Data keys: " + keys.slice(0, 10).join(", "));
                            }
                        }
                    } catch (e) {
                        // Not JSON
                    }
                }

                console.log("─".repeat(70) + "\n");
            }

            return response;
        };
    });

    console.log("[✓] Hooking complete!");
    console.log("\n📱 Now browse dramas and navigate episodes in the app");
    console.log("📊 Type: status()        - Show capture count");
    console.log("📋 Type: lastRequest()   - Show last captured request");
    console.log("💾 Type: exportAll()     - Export all API calls as JSON\n");
});

// === RPC EXPORTS ===
rpc.exports = {
    status: function () {
        console.log("\n📊 Captured " + capturedRequests.length + " API requests\n");
        return "Total requests: " + capturedRequests.length;
    },

    lastRequest: function () {
        if (capturedRequests.length === 0) {
            console.log("\n❌ No requests captured yet\n");
            return null;
        }

        var last = capturedRequests[capturedRequests.length - 1];
        console.log("\n" + "=".repeat(70));
        console.log("LAST REQUEST (#" + last.id + ")");
        console.log("=".repeat(70));
        console.log(JSON.stringify(last, null, 2));
        console.log("=".repeat(70) + "\n");

        return last;
    },

    exportAll: function () {
        console.log("\n" + "=".repeat(70));
        console.log("EXPORT ALL CAPTURED API REQUESTS");
        console.log("=".repeat(70));
        console.log("Total: " + capturedRequests.length + " requests");
        console.log("=".repeat(70));
        console.log(JSON.stringify({
            totalRequests: capturedRequests.length,
            capturedAt: new Date().toISOString(),
            requests: capturedRequests
        }, null, 2));
        console.log("=".repeat(70) + "\n");

        return {
            totalRequests: capturedRequests.length,
            requests: capturedRequests
        };
    },

    getRequestsByUrl: function (urlPattern) {
        var filtered = capturedRequests.filter(function (req) {
            return req.url.indexOf(urlPattern) !== -1;
        });

        console.log("\n📋 Found " + filtered.length + " requests matching: " + urlPattern + "\n");
        console.log(JSON.stringify(filtered, null, 2));

        return filtered;
    }
};
