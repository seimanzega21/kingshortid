/**
 * PROFESSIONAL COVER CAPTURER
 * Uses TESTED working pattern from capture-metadata.js
 */

console.log("\n" + "=".repeat(70));
console.log("🎯 Professional Cover URL Capturer");
console.log("=".repeat(70) + "\n");

var capturedCovers = [];
var capturedMetadata = {};

Java.perform(function () {
    var RealInterceptorChain = Java.use("okhttp3.internal.http.RealInterceptorChain");
    var ResponseBody = Java.use("okhttp3.ResponseBody");

    // Use EXACT working pattern
    RealInterceptorChain.proceed.overloads.forEach(function (method) {
        method.implementation = function () {
            var request = this.request();
            var url = request.toString();
            var response = null;

            // Call original
            if (arguments.length === 0) {
                response = this.proceed();
            } else {
                response = this.proceed(arguments[0]);
            }

            // ==================== CAPTURE COVER URLS ====================
            // Pattern: acf.goodreels.com/videobook/{bookId}/cover_*
            if (url.indexOf("acf.goodreels.com/videobook") !== -1 &&
                url.indexOf("cover") !== -1) {

                var cleanUrl = url.split('?')[0]; // Remove query params

                // Extract book ID
                var bookIdMatch = url.match(/\/(\d{11,})\//);
                var bookId = bookIdMatch ? bookIdMatch[1] : 'unknown';

                if (capturedCovers.indexOf(cleanUrl) === -1) {
                    capturedCovers.push(cleanUrl);

                    console.log("\n🖼️  COVER CAPTURED!");
                    console.log("   Book ID: " + bookId);
                    console.log("   URL: " + cleanUrl);

                    if (!capturedMetadata[bookId]) {
                        capturedMetadata[bookId] = {
                            bookId: bookId,
                            coverUrl: cleanUrl,
                            capturedAt: new Date().toISOString()
                        };
                    } else if (!capturedMetadata[bookId].coverUrl) {
                        capturedMetadata[bookId].coverUrl = cleanUrl;
                    }
                }
            }

            // ==================== CAPTURE METADATA ====================
            if (url.indexOf("api-akm.goodreels.com") !== -1 ||
                url.indexOf("hwycclientreels") !== -1) {
                try {
                    var body = response.body();
                    if (body) {
                        var bodyStr = body.string();

                        // Rebuild response
                        var mediaType = body.contentType();
                        var newBody = ResponseBody.create(mediaType, bodyStr);
                        response = response.newBuilder().body(newBody).build();

                        if (bodyStr.length > 0 && bodyStr.length < 100000) {
                            try {
                                var json = JSON.parse(bodyStr);

                                // Book detail API
                                if (json.data && json.data.id && !Array.isArray(json.data)) {
                                    var book = json.data;
                                    var bookId = book.id.toString();

                                    if (!capturedMetadata[bookId]) {
                                        capturedMetadata[bookId] = {};
                                    }

                                    capturedMetadata[bookId].bookId = bookId;
                                    capturedMetadata[bookId].title = book.title || book.name || null;
                                    capturedMetadata[bookId].genre = book.category || book.categoryName || null;
                                    capturedMetadata[bookId].description = book.description || book.intro || null;

                                    console.log("\n📚 METADATA CAPTURED!");
                                    console.log("   Title: " + capturedMetadata[bookId].title);
                                    console.log("   Genre: " + capturedMetadata[bookId].genre);
                                }

                            } catch (parseErr) {
                                // Not JSON
                            }
                        }
                    }
                } catch (bodyErr) {
                    // Body read error
                }
            }

            return response;
        };
    });

    console.log("[✓] Cover capturer running!");
    console.log("\n📱 Browse dramas now - covers will auto-capture\n");
});

// RPC exports
rpc.exports = {
    status: function () {
        console.log("\n" + "=".repeat(70));
        console.log("📊 CAPTURE STATUS");
        console.log("=".repeat(70));
        console.log("Cover URLs: " + capturedCovers.length);
        console.log("Dramas: " + Object.keys(capturedMetadata).length);
        console.log("=".repeat(70) + "\n");

        return {
            totalCovers: capturedCovers.length,
            totalDramas: Object.keys(capturedMetadata).length
        };
    },

    listCovers: function () {
        console.log("\n" + "=".repeat(70));
        console.log("CAPTURED COVER URLS (" + capturedCovers.length + ")");
        console.log("=".repeat(70));

        capturedCovers.forEach(function (url, i) {
            console.log((i + 1) + ". " + url);
        });

        return capturedCovers;
    },

    listDramas: function () {
        console.log("\n" + "=".repeat(70));
        console.log("CAPTURED DRAMAS (" + Object.keys(capturedMetadata).length + ")");
        console.log("=".repeat(70));

        for (var bookId in capturedMetadata) {
            var drama = capturedMetadata[bookId];
            console.log("\n" + bookId + ":");
            console.log("  Title: " + (drama.title || "N/A"));
            console.log("  Cover: " + (drama.coverUrl || "N/A"));
            console.log("  Genre: " + (drama.genre || "N/A"));
        }

        return capturedMetadata;
    },

    exportData: function () {
        console.log("\n" + "=".repeat(70));
        console.log("EXPORT DATA");
        console.log("=".repeat(70));
        console.log(JSON.stringify(capturedMetadata, null, 2));
        console.log("=".repeat(70) + "\n");

        console.log("💾 To save, copy this JSON and save to covers_data.json");

        return capturedMetadata;
    }
};

// Global shortcuts
globalThis.status = function () { return rpc.exports.status(); };
globalThis.covers = function () { return rpc.exports.listCovers(); };
globalThis.dramas = function () { return rpc.exports.listDramas(); };
globalThis.exportData = function () { return rpc.exports.exportData(); };
