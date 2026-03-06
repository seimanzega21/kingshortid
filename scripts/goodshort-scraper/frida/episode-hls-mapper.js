/**
 * Perfect Episode-HLS Mapper
 * ===========================
 * 
 * Strategy: Track episode order and map HLS URLs to episode numbers
 * as user taps through episodes sequentially
 */

console.log("\n" + "=".repeat(70));
console.log("🎯 Perfect Episode-HLS Mapper");
console.log("=".repeat(70) + "\n");

var capturedDramas = {};
var currentBookId = null;
var episodeCounter = 0;

Java.perform(function () {
    var RealInterceptorChain = Java.use("okhttp3.internal.http.RealInterceptorChain");
    var ResponseBody = Java.use("okhttp3.ResponseBody");

    RealInterceptorChain.proceed.overloads.forEach(function (method) {
        method.implementation = function () {
            var request = this.request();
            var url = request.toString();
            var response = null;

            if (arguments.length === 0) {
                response = this.proceed();
            } else {
                response = this.proceed(arguments[0]);
            }

            try {
                // ===== CAPTURE BOOK METADATA =====
                if (url.indexOf("api-akm.goodreels.com") !== -1) {
                    var body = response.body();
                    if (body) {
                        var bodyStr = body.string();
                        var mediaType = body.contentType();
                        response = response.newBuilder().body(ResponseBody.create(mediaType, bodyStr)).build();

                        try {
                            var json = JSON.parse(bodyStr);

                            // Book detail
                            if (json.data && json.data.id && json.data.title) {
                                var book = json.data;
                                var bookId = book.id.toString();

                                if (!capturedDramas[bookId]) {
                                    capturedDramas[bookId] = {
                                        bookId: bookId,
                                        title: book.title,
                                        description: book.description || book.intro,
                                        totalEpisodes: book.chapterCount || 0,
                                        coverUrl: null,
                                        episodes: {}
                                    };

                                    currentBookId = bookId;
                                    episodeCounter = 0;

                                    console.log("\n📚 DRAMA: " + book.title);
                                    console.log("   ID: " + bookId);
                                    console.log("   Total Episodes: " + (book.chapterCount || 0));
                                }
                            }
                        } catch (e) { }
                    }
                }

                // ===== CAPTURE COVER (MAIN POSTER ONLY) =====
                if (url.indexOf("acf.goodreels.com/videobook") !== -1 &&
                    url.indexOf("cover") !== -1 &&
                    url.indexOf("202") !== -1) {  // Main CDN covers

                    var cleanUrl = url.split('?')[0];

                    // Extract book ID from cover URL
                    var bookIdMatch = cleanUrl.match(/\/(\d{11,})\//);
                    var bookId = bookIdMatch ? bookIdMatch[1] : currentBookId;

                    if (bookId && capturedDramas[bookId] && !capturedDramas[bookId].coverUrl) {
                        capturedDramas[bookId].coverUrl = cleanUrl;
                        console.log("🖼️  Cover captured");
                    }
                }

                // ===== CAPTURE HLS + MAP TO EPISODE =====
                if (url.indexOf(".m3u8") !== -1 && url.indexOf("goodreels.com") !== -1) {
                    var cleanUrl = url.split('?')[0];

                    // Extract episode ID from HLS URL
                    var episodeIdMatch = cleanUrl.match(/\/(\d+)\/[^\/]+\/720p/);
                    var episodeId = episodeIdMatch ? episodeIdMatch[1] : null;

                    if (currentBookId && capturedDramas[currentBookId]) {
                        // Increment episode counter (assumes sequential tapping)
                        episodeCounter++;

                        var episodeNum = episodeCounter;

                        // Store episode data
                        capturedDramas[currentBookId].episodes[episodeNum] = {
                            episodeNumber: episodeNum,
                            episodeId: episodeId,
                            hlsUrl: cleanUrl,
                            title: "Episode " + episodeNum
                        };

                        console.log("🎥 Episode " + episodeNum + " → HLS captured");
                        console.log("   " + cleanUrl.substring(cleanUrl.length - 50));
                    }
                }

            } catch (e) { }

            return response;
        };
    });

    console.log("[✓] Episode-HLS mapper ready!");
    console.log("📱 Tap drama, then tap each episode 1,2,3...\n");
});

rpc.exports = {
    resetCounter: function () {
        episodeCounter = 0;
        console.log("✅ Episode counter reset to 0");
    },

    status: function () {
        console.log("\n" + "=".repeat(60));
        console.log("📊 CAPTURED DATA");
        console.log("=".repeat(60));

        for (var bookId in capturedDramas) {
            var drama = capturedDramas[bookId];
            var epCount = Object.keys(drama.episodes).length;

            console.log("\n📚 " + drama.title);
            console.log("   ID: " + bookId);
            console.log("   Episodes captured: " + epCount + "/" + drama.totalEpisodes);
            console.log("   Cover: " + (drama.coverUrl ? "✅" : "❌"));

            if (epCount > 0) {
                console.log("\n   Episodes:");
                var epNums = Object.keys(drama.episodes).sort(function (a, b) { return a - b; });
                for (var i = 0; i < Math.min(5, epNums.length); i++) {
                    var num = epNums[i];
                    var ep = drama.episodes[num];
                    console.log("   " + num + ". Episode " + num + " ✅ HLS");
                }
                if (epCount > 5) {
                    console.log("   ... and " + (epCount - 5) + " more");
                }
            }
        }

        console.log("\n" + "=".repeat(60) + "\n");
        return capturedDramas;
    },

    export: function () {
        return capturedDramas;
    }
};
