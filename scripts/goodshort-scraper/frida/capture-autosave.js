/**
 * Frida Auto-Save Capture Script v2
 * 
 * Automatically captures and saves episode URLs to a JSON file.
 * Uses Android File API to write directly to device storage.
 * 
 * Usage:
 * 1. Run: frida -U -p [PID] -l frida\capture-autosave.js
 * 2. Browse dramas and episodes in the app
 * 3. Episodes are auto-captured and displayed
 * 4. When done, type: exportData() to get the JSON
 */

console.log("\n" + "=".repeat(60));
console.log("[*] GoodShort Episode Collector v2 - Auto Save");
console.log("[*] Browse dramas & episodes - URLs will be auto-captured");
console.log("=".repeat(60) + "\n");

// Store captured data
var capturedData = {
    dramas: {},
    lastUpdate: null,
    stats: {
        totalDramas: 0,
        totalEpisodes: 0
    }
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

    // Also try m3u8 pattern
    var m3u8Match = url.match(/\/mts\/books\/(\d+)\/(\d+)\/(\d+)\/([a-z0-9]+)\/(\d+p)\/([a-z0-9]+)_\d+p\.m3u8/i);
    if (m3u8Match) {
        return {
            bookId: m3u8Match[2],
            chapterId: m3u8Match[3],
            token: m3u8Match[4],
            resolution: m3u8Match[5],
            videoId: m3u8Match[6]
        };
    }

    return null;
}

// Parse cover URL
function parseCoverUrl(url) {
    // Pattern: /videobook/{bookId}/YYYYMM/cover-{id}.jpg or /videobook/YYYYMM/cover-{id}.jpg
    if (url.indexOf("acf.goodreels.com/videobook") !== -1) {
        return url.split('?')[0];  // Remove query params
    }
    return null;
}

// Update stats
function updateStats() {
    capturedData.stats.totalDramas = Object.keys(capturedData.dramas).length;
    capturedData.stats.totalEpisodes = 0;
    for (var d in capturedData.dramas) {
        capturedData.stats.totalEpisodes += Object.keys(capturedData.dramas[d].episodes).length;
    }
}

// Print status bar
function printStatus() {
    updateStats();
    console.log("\n┌─────────────────────────────────────────────────────────┐");
    console.log("│  📊 CAPTURE STATUS                                      │");
    console.log("├─────────────────────────────────────────────────────────┤");
    console.log("│  Dramas: " + capturedData.stats.totalDramas.toString().padEnd(5) + "     Episodes: " + capturedData.stats.totalEpisodes.toString().padEnd(20) + "│");
    console.log("└─────────────────────────────────────────────────────────┘\n");
}

Java.perform(function () {

    var RealInterceptorChain = Java.use("okhttp3.internal.http.RealInterceptorChain");

    RealInterceptorChain.proceed.overloads.forEach(function (method) {
        method.implementation = function () {
            var request = this.request();
            var url = request.toString();

            // Capture video segment URLs (both .ts and .m3u8)
            if (url.indexOf("v2-akm.goodreels.com/mts/books") !== -1) {
                var parsed = parseVideoUrl(url);
                if (parsed) {
                    var bookId = parsed.bookId;
                    var chapterId = parsed.chapterId;

                    // Initialize drama entry if needed
                    if (!capturedData.dramas[bookId]) {
                        capturedData.dramas[bookId] = {
                            bookId: bookId,
                            title: "Drama " + bookId,
                            cover: null,
                            episodes: {}
                        };
                        console.log("\n🎬 [NEW DRAMA] Book ID: " + bookId);
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
                        console.log("   📺 Episode " + episodeCount + " captured (Chapter: " + chapterId + ")");

                        capturedData.lastUpdate = new Date().toISOString();

                        // Print status every 5 episodes
                        updateStats();
                        if (capturedData.stats.totalEpisodes % 5 === 0) {
                            printStatus();
                        }
                    }
                }
            }

            // Capture cover images
            if (url.indexOf("acf.goodreels.com/videobook") !== -1 && url.indexOf("cover-") !== -1) {
                var coverUrl = parseCoverUrl(url);
                if (coverUrl) {
                    // Try to match with a drama
                    // Pattern 1: /videobook/{bookId}/YYYYMM/cover-xxx.jpg
                    var bookMatch = coverUrl.match(/\/videobook\/(\d{11})\/\d+\/cover-/);
                    if (bookMatch && capturedData.dramas[bookMatch[1]]) {
                        if (!capturedData.dramas[bookMatch[1]].cover) {
                            capturedData.dramas[bookMatch[1]].cover = coverUrl;
                            console.log("   🖼️  Cover captured for drama " + bookMatch[1]);
                        }
                    } else {
                        // Assign to most recent drama without cover
                        var dramaIds = Object.keys(capturedData.dramas);
                        for (var i = dramaIds.length - 1; i >= 0; i--) {
                            if (!capturedData.dramas[dramaIds[i]].cover) {
                                capturedData.dramas[dramaIds[i]].cover = coverUrl;
                                console.log("   🖼️  Cover captured for drama " + dramaIds[i]);
                                break;
                            }
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

    console.log("[✓] Hooking complete!\n");
    console.log("📱 Now browse dramas and swipe through episodes in the app");
    console.log("📊 Type: status()     - Show capture statistics");
    console.log("📋 Type: list()       - List all captured dramas");
    console.log("💾 Type: exportData() - Export JSON (copy this to captured-episodes.json)");
    console.log("");
});

// Helper functions for console
this.status = function () {
    printStatus();
    return "Status printed above";
};

this.list = function () {
    console.log("\n=== CAPTURED DRAMAS ===");
    for (var bookId in capturedData.dramas) {
        var drama = capturedData.dramas[bookId];
        var epCount = Object.keys(drama.episodes).length;
        console.log("  📹 " + bookId + ": " + epCount + " episodes" + (drama.cover ? " ✓cover" : " ⚠no cover"));
    }
    console.log("=======================\n");
    return "List printed above";
};

this.exportData = function () {
    capturedData.lastUpdate = new Date().toISOString();
    updateStats();

    console.log("\n" + "=".repeat(60));
    console.log("COPY THE JSON BELOW AND SAVE TO: captured-episodes.json");
    console.log("=".repeat(60));
    console.log(JSON.stringify(capturedData, null, 2));
    console.log("=".repeat(60) + "\n");

    return "JSON exported above. Copy and save to captured-episodes.json";
};

// Shorthand
this.s = this.status;
this.l = this.list;
this.e = this.exportData;

// Export data object
this.data = capturedData;
