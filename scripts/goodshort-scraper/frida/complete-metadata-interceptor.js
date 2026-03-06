/**
 * Optimized Complete Metadata Interceptor
 * ========================================
 * 
 * FIXED ISSUES:
 * - Only capture 1 poster per drama (not episode thumbnails)
 * - Focus on episode list API to get episode 1,2,3... with HLS URLs
 * - Better API endpoint detection
 */

console.log("\n" + "=".repeat(70));
console.log("🎬 Optimized Metadata Interceptor - Episode Focus");
console.log("=".repeat(70) + "\n");

var dramaData = {};
var currentDrama = null;

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
                // ========== 1. CAPTURE MAIN DRAMA POSTER ONLY ==========
                // Only capture large cover images (main poster), skip thumbnails
                if (url.indexOf("acf.goodreels.com") !== -1 &&
                    url.indexOf("cover") !== -1 &&
                    url.indexOf("202") !== -1) {  // CDN pattern with date

                    var cleanUrl = url.split('?')[0];

                    // Extract hash from cover URL
                    var hashMatch = cleanUrl.match(/cover-([^.\/]+)/);
                    if (hashMatch) {
                        var hash = hashMatch[1];

                        // Only store if not already stored (prevent duplicates)
                        var alreadyStored = false;
                        for (var id in dramaData) {
                            if (dramaData[id].coverUrl && dramaData[id].coverUrl.indexOf(hash) !== -1) {
                                alreadyStored = true;
                                break;
                            }
                        }

                        if (!alreadyStored) {
                            if (!currentDrama) {
                                currentDrama = hash; // Temporary ID
                                dramaData[currentDrama] = {
                                    coverUrl: cleanUrl,
                                    episodes: [],
                                    hlsUrls: []
                                };
                            } else if (!dramaData[currentDrama].coverUrl) {
                                dramaData[currentDrama].coverUrl = cleanUrl;
                            }

                            console.log("🖼️  POSTER: " + cleanUrl.substring(cleanUrl.length - 40));
                        }
                    }
                }

                // ========== 2. CAPTURE BOOK METADATA API ==========
                if (url.indexOf("api-akm.goodreels.com") !== -1) {
                    var body = response.body();
                    if (body) {
                        var bodyStr = body.string();
                        var mediaType = body.contentType();
                        response = response.newBuilder().body(ResponseBody.create(mediaType, bodyStr)).build();

                        try {
                            var json = JSON.parse(bodyStr);

                            // Book detail API
                            if (json.data && json.data.id && json.data.title) {
                                var book = json.data;
                                var bookId = book.id.toString();

                                if (!dramaData[bookId]) {
                                    dramaData[bookId] = {
                                        episodes: [],
                                        hlsUrls: []
                                    };
                                }

                                dramaData[bookId].bookId = bookId;
                                dramaData[bookId].title = book.title || book.name;
                                dramaData[bookId].description = book.description || book.intro;
                                dramaData[bookId].genre = book.category || book.genreName;
                                dramaData[bookId].tags = book.tags || book.labels || [];
                                dramaData[bookId].totalEpisodes = book.chapterCount || book.episodeCount || 0;

                                currentDrama = bookId;

                                console.log("\n📚 DRAMA: " + dramaData[bookId].title);
                                console.log("   ID: " + bookId);
                                console.log("   Episodes: " + dramaData[bookId].totalEpisodes);
                            }

                            // Chapter/Episode list API
                            if (json.data && Array.isArray(json.data)) {
                                var list = json.data;

                                // Check if this is episode list
                                if (list.length > 0 && (list[0].chapterId || list[0].chapterIndex !== undefined)) {
                                    var bookId = currentDrama;

                                    if (bookId && dramaData[bookId]) {
                                        console.log("\n📺 EPISODE LIST: " + list.length + " episodes");

                                        dramaData[bookId].episodes = [];

                                        for (var i = 0; i < list.length; i++) {
                                            var ep = list[i];
                                            dramaData[bookId].episodes.push({
                                                episodeNumber: ep.chapterIndex !== undefined ? ep.chapterIndex : (i + 1),
                                                episodeId: ep.id || ep.chapterId,
                                                title: ep.title || ep.chapterTitle || ("Episode " + (i + 1)),
                                                duration: ep.duration || 0
                                            });
                                        }

                                        console.log("   ✅ Captured episodes 1-" + list.length);
                                    }
                                }
                            }
                        } catch (e) { }
                    }
                }

                // ========== 3. CAPTURE HLS VIDEO URLS ==========
                if (url.indexOf(".m3u8") !== -1 && url.indexOf("goodreels.com") !== -1) {
                    var cleanUrl = url.split('?')[0];

                    // Extract episode ID from URL path
                    var pathMatch = cleanUrl.match(/\/(\d+)\/[^\/]+\/720p/);
                    var episodeId = pathMatch ? pathMatch[1] : null;

                    console.log("\n🎥 HLS: Episode " + (episodeId || "unknown"));
                    console.log("   " + cleanUrl);

                    if (currentDrama && dramaData[currentDrama]) {
                        // Try to match HLS URL with episode
                        if (episodeId && dramaData[currentDrama].episodes) {
                            for (var i = 0; i < dramaData[currentDrama].episodes.length; i++) {
                                var ep = dramaData[currentDrama].episodes[i];
                                if (ep.episodeId && ep.episodeId.toString() === episodeId) {
                                    ep.hlsUrl = cleanUrl;
                                    console.log("   ✅ Matched to Episode " + ep.episodeNumber);
                                    break;
                                }
                            }
                        }

                        // Also store in array
                        if (!dramaData[currentDrama].hlsUrls) {
                            dramaData[currentDrama].hlsUrls = [];
                        }
                        dramaData[currentDrama].hlsUrls.push(cleanUrl);
                    }
                }

            } catch (e) { }

            return response;
        };
    });

    console.log("[✓] Optimized interceptor running!");
    console.log("📱 Browse drama + scroll episodes\n");
});

rpc.exports = {
    status: function () {
        console.log("\n📊 CAPTURED DATA:\n");

        for (var id in dramaData) {
            var d = dramaData[id];
            console.log("━".repeat(60));
            console.log("Drama: " + (d.title || id));
            console.log("Episodes captured: " + (d.episodes ? d.episodes.length : 0));
            console.log("HLS URLs: " + (d.hlsUrls ? d.hlsUrls.length : 0));

            if (d.episodes && d.episodes.length > 0) {
                console.log("\nEpisodes:");
                for (var i = 0; i < Math.min(5, d.episodes.length); i++) {
                    var ep = d.episodes[i];
                    console.log("  " + ep.episodeNumber + ". " + ep.title +
                        (ep.hlsUrl ? " ✅" : " ⏳"));
                }
                if (d.episodes.length > 5) {
                    console.log("  ... and " + (d.episodes.length - 5) + " more");
                }
            }
        }

        console.log("━".repeat(60) + "\n");
        return dramaData;
    },

    export: function () {
        console.log(JSON.stringify(dramaData, null, 2));
        return dramaData;
    }
};
