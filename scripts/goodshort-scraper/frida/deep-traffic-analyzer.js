/**
 * Professional Cover URL Capturer
 * Captures REAL cover poster URLs from network traffic
 */

console.log("\n🔍 Professional Network Analyzer - Cover URL Capturer\n");

var captured = {
    coverUrls: [],
    apiData: []
};

Java.perform(function () {
    var RealInterceptorChain = Java.use("okhttp3.internal.http.RealInterceptorChain");
    var ResponseBody = Java.use("okhttp3.ResponseBody");

    // Use the request() method approach like in working script
    RealInterceptorChain.proceed.implementation = function (request) {
        var url = request.url().toString();
        var response = this.proceed(request);

        // IMAGE URLs - potential covers
        if (url.match(/\.(jpg|jpeg|png|webp)/i) || url.indexOf('cover') !== -1 || url.indexOf('acf.goodreels') !== -1) {
            captured.coverUrls.push(url);
            console.log("\n🖼️  IMAGE: " + url);
        }

        // API responses with metadata
        if (url.indexOf('api') !== -1 || url.indexOf('goodreels') !== -1) {
            try {
                var body = response.body();
                if (body) {
                    var bodyStr = body.string();
                    var mediaType = body.contentType();
                    response = response.newBuilder().body(ResponseBody.create(mediaType, bodyStr)).build();

                    try {
                        var json = JSON.parse(bodyStr);
                        if (bodyStr.length < 50000) {
                            console.log("\n📡 API: " + url);
                            console.log("   Keys: " + Object.keys(json).join(', '));

                            captured.apiData.push({ url: url, data: json });
                        }
                    } catch (e) { }
                }
            } catch (e) { }
        }

        return response;
    };

    console.log("[✓] Analyzer running - Open drama detail page now!\n");
});

rpc.exports = {
    getCovers: function () {
        console.log("\n" + "=".repeat(70));
        console.log("CAPTURED COVER URLs (" + captured.coverUrls.length + ")");
        console.log("=".repeat(70));
        captured.coverUrls.forEach(function (u, i) {
            console.log((i + 1) + ". " + u);
        });
        return captured.coverUrls;
    },

    getApis: function () {
        console.log("\n" + "=".repeat(70));
        console.log("API RESPONSES (" + captured.apiData.length + ")");
        console.log("=".repeat(70));
        captured.apiData.forEach(function (a, i) {
            console.log("\n" + (i + 1) + ". " + a.url);
            console.log(JSON.stringify(a.data, null, 2).substring(0, 500));
        });
        return captured.apiData;
    },

    export: function () {
        return captured;
    }
};

globalThis.covers = function () { return rpc.exports.getCovers(); };
globalThis.apis = function () { return rpc.exports.getApis(); };
globalThis.export = function () { return rpc.exports.export(); };
