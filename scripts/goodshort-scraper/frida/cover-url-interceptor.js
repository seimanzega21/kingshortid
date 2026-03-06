/**
 * Professional Cover URL Interceptor with Auto-Save
 * Captures cover CDN URLs and saves to JSON file automatically
 */

console.log("\n" + "=".repeat(70));
console.log("🎯 Professional Cover CDN Interceptor");
console.log("=".repeat(70) + "\n");

var coverData = {};
var fs = null;
var outputFile = "/sdcard/covers_urls.json";

// Initialize filesystem access
try {
    fs = Java.use("java.io.FileWriter");
    console.log("[✓] Filesystem access ready");
} catch (e) {
    console.log("[!] Filesystem not available, will export manually");
}

function saveToFile() {
    if (!fs) return;

    try {
        var jsonStr = JSON.stringify(coverData, null, 2);
        var writer = fs.$new(outputFile, false);
        writer.write(jsonStr);
        writer.close();
        console.log("💾 Auto-saved to: " + outputFile);
    } catch (e) {
        console.log("⚠️  Auto-save failed: " + e);
    }
}

Java.perform(function () {
    var RealInterceptorChain = Java.use("okhttp3.internal.http.RealInterceptorChain");
    var ResponseBody = Java.use("okhttp3.ResponseBody");

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

            // ========== CAPTURE COVER IMAGES ==========
            // Pattern 1: acf.goodreels.com/videobook/.../cover
            // Pattern 2: cdn URLs with image extensions
            if ((url.indexOf("acf.goodreels.com") !== -1 && url.indexOf("cover") !== -1) ||
                (url.indexOf("goodreels") !== -1 && url.match(/\.(jpg|jpeg|png|webp)/i))) {

                var cleanUrl = url.split('?')[0];

                // Extract book ID from URL
                var bookIdMatch = url.match(/\/(\d{11,})\//);
                var bookId = bookIdMatch ? bookIdMatch[1] : null;

                // If no book ID in URL, try to extract from path
                if (!bookId) {
                    var pathMatch = url.match(/cover-([^.\/]+)/);
                    if (pathMatch) {
                        bookId = pathMatch[1];
                    }
                }

                if (bookId) {
                    if (!coverData[bookId]) {
                        coverData[bookId] = {
                            bookId: bookId,
                            coverUrls: [],
                            capturedAt: new Date().toISOString()
                        };
                    }

                    if (coverData[bookId].coverUrls.indexOf(cleanUrl) === -1) {
                        coverData[bookId].coverUrls.push(cleanUrl);

                        console.log("\n🖼️  COVER CAPTURED!");
                        console.log("   Book ID: " + bookId);
                        console.log("   URL: " + cleanUrl);
                        console.log("   Total covers: " + Object.keys(coverData).length);

                        // Auto-save after each capture
                        saveToFile();
                    }
                }
            }

            // ========== CAPTURE METADATA ==========
            if (url.indexOf("api-akm.goodreels.com") !== -1) {
                try {
                    var body = response.body();
                    if (body) {
                        var bodyStr = body.string();
                        var mediaType = body.contentType();
                        response = response.newBuilder().body(ResponseBody.create(mediaType, bodyStr)).build();

                        try {
                            var json = JSON.parse(bodyStr);

                            if (json.data && json.data.id) {
                                var book = json.data;
                                var bookId = book.id.toString();

                                if (!coverData[bookId]) {
                                    coverData[bookId] = {
                                        bookId: bookId,
                                        coverUrls: [],
                                        capturedAt: new Date().toISOString()
                                    };
                                }

                                coverData[bookId].title = book.title || book.name || null;
                                coverData[bookId].genre = book.category || null;

                                console.log("\n📚 METADATA: " + coverData[bookId].title);

                                // Auto-save
                                saveToFile();
                            }
                        } catch (e) { }
                    }
                } catch (e) { }
            }

            return response;
        };
    });

    console.log("[✓] Cover interceptor running!");
    console.log("📱 Browse dramas - covers will auto-capture\n");
    console.log("💾 Output: " + outputFile);
    console.log("📥 Pull with: adb pull " + outputFile + "\n");
});

// RPC exports for manual control
rpc.exports = {
    status: function () {
        console.log("\n" + "=".repeat(70));
        console.log("📊 CAPTURE STATUS");
        console.log("=".repeat(70));
        console.log("Dramas captured: " + Object.keys(coverData).length);

        for (var id in coverData) {
            var drama = coverData[id];
            console.log("\n" + id + ":");
            console.log("  Title: " + (drama.title || "N/A"));
            console.log("  Covers: " + drama.coverUrls.length);
        }

        console.log("=".repeat(70) + "\n");
        return coverData;
    },

    save: function () {
        saveToFile();
        console.log("✅ Manual save complete");
        return true;
    },

    export: function () {
        console.log("\n" + JSON.stringify(coverData, null, 2));
        return coverData;
    }
};
