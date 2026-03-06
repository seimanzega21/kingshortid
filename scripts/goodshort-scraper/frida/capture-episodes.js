/**
 * Frida Capture Script - Auto-save Episode URLs
 * 
 * This script captures video URLs and saves them to a file
 * that can be used by the batch downloader.
 * 
 * Usage:
 * 1. Run: frida -U -p [PID] -l frida\capture-episodes.js
 * 2. Browse dramas and open episodes in the app
 * 3. Check captured-episodes.json for collected URLs
 */

console.log("\n" + "=".repeat(60));
console.log("[*] GoodShort Episode URL Collector v1");
console.log("[*] Browse dramas & episodes - URLs will be auto-captured");
console.log("=".repeat(60) + "\n");

// Store captured data
var capturedData = {
    dramas: {},
    lastUpdate: null
};

// Parse video URL to extract components
function parseVideoUrl(url) {
    // Pattern: /mts/books/{xxx}/{bookId}/{chapterId}/{token}/720p/{videoId}_720p_{segment}.ts
    var match = url.match(/\/mts\/books\/(\d+)\/(\d+)\/(\d+)\/([a-z0-9]+)\/(\d+p)\/([a-z0-9]+)_\d+p_\d+\.ts/i);
    if (match) {
        return {
            bookId: match[2],
            chapterId: match[3],
            token: match[4],
            resolution: match[5],
            videoId: match[6]
        };
    }
    return null;
}

// Parse cover URL
function parseCoverUrl(url) {
    // Pattern: /videobook/YYYYMM/cover-{id}.jpg
    var match = url.match(/acf\.goodreels\.com\/videobook\/(\d+)\/(cover-[a-zA-Z0-9]+\.jpg)/);
    if (match) {
        return {
            folder: match[1],
            filename: match[2],
            fullUrl: url.split('?')[0]  // Remove query params
        };
    }
    return null;
}

Java.perform(function () {

    var RealInterceptorChain = Java.use("okhttp3.internal.http.RealInterceptorChain");

    RealInterceptorChain.proceed.overloads.forEach(function (method) {
        method.implementation = function () {
            var request = this.request();
            var url = request.toString();

            // Capture video segment URLs
            if (url.indexOf("v2-akm.goodreels.com/mts/books") !== -1) {
                var parsed = parseVideoUrl(url);
                if (parsed) {
                    var bookId = parsed.bookId;
                    var chapterId = parsed.chapterId;

                    // Initialize drama entry if needed
                    if (!capturedData.dramas[bookId]) {
                        capturedData.dramas[bookId] = {
                            bookId: bookId,
                            title: "Unknown",
                            cover: null,
                            episodes: {}
                        };
                        console.log("\n[NEW DRAMA] Book ID: " + bookId);
                    }

                    // Add episode if not exists
                    if (!capturedData.dramas[bookId].episodes[chapterId]) {
                        capturedData.dramas[bookId].episodes[chapterId] = {
                            chapterId: chapterId,
                            token: parsed.token,
                            videoId: parsed.videoId,
                            resolution: parsed.resolution
                        };

                        var episodeCount = Object.keys(capturedData.dramas[bookId].episodes).length;
                        console.log("[EPISODE] Drama " + bookId + " - Chapter " + chapterId + " (Total: " + episodeCount + " episodes)");

                        // Print current stats
                        var totalDramas = Object.keys(capturedData.dramas).length;
                        var totalEpisodes = 0;
                        for (var d in capturedData.dramas) {
                            totalEpisodes += Object.keys(capturedData.dramas[d].episodes).length;
                        }
                        console.log("[STATS] " + totalDramas + " dramas, " + totalEpisodes + " episodes captured\n");
                    }

                    capturedData.lastUpdate = new Date().toISOString();
                }
            }

            // Capture cover images
            if (url.indexOf("acf.goodreels.com/videobook") !== -1) {
                var coverParsed = parseCoverUrl(url);
                if (coverParsed) {
                    // Try to associate with most recent drama
                    // (This is a heuristic - covers usually load after drama is opened)
                    var dramaIds = Object.keys(capturedData.dramas);
                    if (dramaIds.length > 0) {
                        var lastDrama = dramaIds[dramaIds.length - 1];
                        if (!capturedData.dramas[lastDrama].cover) {
                            capturedData.dramas[lastDrama].cover = coverParsed.fullUrl;
                            console.log("[COVER] " + coverParsed.fullUrl.substring(0, 60) + "...");
                        }
                    }
                }
            }

            // Call original
            if (arguments.length === 0) {
                return this.proceed();
            } else {
                return this.proceed(arguments[0]);
            }
        };
    });

    console.log("[+] Hooking complete!");
    console.log("[*] Now browse dramas and open episodes in the app");
    console.log("[*] Type 'show()' to see captured data");
    console.log("[*] Type 'save()' to save to JSON (copy from console)\n");
});

// Helper to show current data
this.show = function () {
    console.log("\n=== CAPTURED DATA ===");
    console.log(JSON.stringify(capturedData, null, 2));
    console.log("=====================\n");
    return capturedData;
};

// Helper to get saveable JSON
this.save = function () {
    console.log("\n=== COPY THIS JSON ===");
    console.log(JSON.stringify(capturedData));
    console.log("======================\n");
    return "Copy the JSON above and save to captured-episodes.json";
};

// Export for REPL
this.data = capturedData;
