/**
 * Frida Enhanced Metadata Capture Script v3
 * 
 * Captures:
 * - Video URLs (from CDN requests)
 * - Cover images  
 * - Drama metadata (title, description, etc.) from API responses
 * - Episode metadata (title, order, etc.)
 * 
 * Focus: Indonesian language dramas
 * 
 * Usage:
 * 1. frida -U -f com.newreading.goodreels -l frida\capture-metadata.js
 * 2. Browse dramas in the app
 * 3. Type: exportData() to get JSON with full metadata
 */

console.log("\n" + "=".repeat(70));
console.log("🚀 GoodShort Auto-Save Collector v3.1");
console.log("📊 Capturing: Videos + Covers + Metadata");
console.log("💾 Auto-Save: Enabled (saves to /sdcard/goodshort_capture.json)");
console.log("=".repeat(70) + "\n");

var SAVE_PATH = "/sdcard/goodshort_capture.json";

// Store captured data with enhanced metadata
var capturedData = {
    session: {
        startTime: new Date().toISOString(),
        lastSave: null,
        autoSaveCount: 0
    },
    dramas: {},
    lastUpdate: null,
    stats: {
        totalDramas: 0,
        totalEpisodes: 0,
        dramasWithMetadata: 0
    }
};

// Auto-save function
function autoSave() {
    try {
        var File = Java.use("java.io.File");
        var FileWriter = Java.use("java.io.FileWriter");

        capturedData.session.lastSave = new Date().toISOString();
        capturedData.session.autoSaveCount++;

        var json = JSON.stringify(capturedData, null, 2);
        var file = File.$new(SAVE_PATH);
        var writer = FileWriter.$new(file);
        writer.write(json);
        writer.close();

        console.log("💾 [AUTO-SAVED #" + capturedData.session.autoSaveCount + "] " + SAVE_PATH);
        return true;
    } catch (e) {
        console.error("❌ Save error: " + e);
        return false;
    }
}

// Parse video URL
function parseVideoUrl(url) {
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
    if (url.indexOf("acf.goodreels.com/videobook") !== -1) {
        return url.split('?')[0];
    }
    return null;
}

// Update stats
function updateStats() {
    capturedData.stats.totalDramas = Object.keys(capturedData.dramas).length;
    capturedData.stats.totalEpisodes = 0;
    capturedData.stats.dramasWithMetadata = 0;

    for (var d in capturedData.dramas) {
        capturedData.stats.totalEpisodes += Object.keys(capturedData.dramas[d].episodes).length;
        if (capturedData.dramas[d].metadata && capturedData.dramas[d].metadata.title) {
            capturedData.stats.dramasWithMetadata++;
        }
    }
}

// Print enhanced status
function printStatus() {
    updateStats();
    console.log("\n┌─────────────────────────────────────────────────────────┐");
    console.log("│  📊 CAPTURE STATUS                                      │");
    console.log("├─────────────────────────────────────────────────────────┤");
    console.log("│  Dramas: " + capturedData.stats.totalDramas.toString().padEnd(5) + "     Episodes: " + capturedData.stats.totalEpisodes.toString().padEnd(20) + "│");
    console.log("│  With Metadata: " + capturedData.stats.dramasWithMetadata.toString().padEnd(42) + "│");
    console.log("└─────────────────────────────────────────────────────────┘\n");
}

Java.perform(function () {

    var RealInterceptorChain = Java.use("okhttp3.internal.http.RealInterceptorChain");
    var Response = Java.use("okhttp3.Response");
    var ResponseBody = Java.use("okhttp3.ResponseBody");

    RealInterceptorChain.proceed.overloads.forEach(function (method) {
        method.implementation = function () {
            var request = this.request();
            var url = request.toString();
            var response = null;

            // Call original to get response
            if (arguments.length === 0) {
                response = this.proceed();
            } else {
                response = this.proceed(arguments[0]);
            }

            // ================== CAPTURE VIDEO URLs ==================
            if (url.indexOf("v2-akm.goodreels.com/mts/books") !== -1) {
                var parsed = parseVideoUrl(url);
                if (parsed) {
                    var bookId = parsed.bookId;
                    var chapterId = parsed.chapterId;

                    // Initialize drama if needed
                    if (!capturedData.dramas[bookId]) {
                        capturedData.dramas[bookId] = {
                            bookId: bookId,
                            title: "Drama " + bookId,
                            cover: null,
                            metadata: null,
                            episodes: {}
                        };
                        console.log("\n🎬 [NEW DRAMA] Book ID: " + bookId);
                    }

                    // Add episode
                    if (!capturedData.dramas[bookId].episodes[chapterId]) {
                        capturedData.dramas[bookId].episodes[chapterId] = {
                            chapterId: chapterId,
                            token: parsed.token,
                            videoId: parsed.videoId,
                            resolution: parsed.resolution,
                            metadata: null
                        };

                        var episodeCount = Object.keys(capturedData.dramas[bookId].episodes).length;
                        console.log("   📺 Episode " + episodeCount + " captured (Chapter: " + chapterId + ")");

                        capturedData.lastUpdate = new Date().toISOString();

                        updateStats();
                        if (capturedData.stats.totalEpisodes % 5 === 0) {
                            printStatus();
                        }
                    }
                }
            }

            // ================== CAPTURE COVER Images ==================
            if (url.indexOf("acf.goodreels.com/videobook") !== -1 && url.indexOf("cover-") !== -1) {
                var coverUrl = parseCoverUrl(url);
                if (coverUrl) {
                    // Try to match bookId from URL
                    var bookMatch = coverUrl.match(/\/videobook\/(\d{11})\/\d+\/cover-/);
                    if (bookMatch && capturedData.dramas[bookMatch[1]]) {
                        if (!capturedData.dramas[bookMatch[1]].cover) {
                            capturedData.dramas[bookMatch[1]].cover = coverUrl;
                            console.log("   🖼️  Cover captured for drama " + bookMatch[1]);
                        }
                    } else {
                        // Assign to most recent drama
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

            // ================== CAPTURE API METADATA ==================
            if (url.indexOf("api-akm.goodreels.com/hwyclientreels") !== -1) {
                try {
                    var responseBody = response.body();
                    var bodyString = responseBody.string();

                    // Re-create response body (since we consumed it)
                    var mediaType = responseBody.contentType();
                    var newBody = ResponseBody.create(mediaType, bodyString);
                    response = response.newBuilder().body(newBody).build();

                    // Try to parse JSON
                    try {
                        var jsonData = JSON.parse(bodyString);

                        // ===== DRAMA DETAIL API =====
                        // Common patterns: /book/detail, /book/info, /book/get
                        if (url.indexOf("/book") !== -1 && jsonData.data) {
                            var bookData = jsonData.data;
                            var bookId = bookData.id || bookData.bookId || bookData.book_id;

                            if (bookId && bookId.toString().length >= 10) {
                                bookId = bookId.toString();

                                // Initialize if not exist
                                if (!capturedData.dramas[bookId]) {
                                    capturedData.dramas[bookId] = {
                                        bookId: bookId,
                                        title: "Drama " + bookId,
                                        cover: null,
                                        metadata: null,
                                        episodes: {}
                                    };
                                }

                                // Extract metadata
                                var metadata = {
                                    title: bookData.title || bookData.name || bookData.bookName || "Drama " + bookId,
                                    description: bookData.description || bookData.desc || bookData.synopsis || "",
                                    cover: bookData.cover || bookData.coverUrl || bookData.image || null,
                                    author: bookData.author || bookData.authorName || null,
                                    totalChapters: bookData.totalChapter || bookData.chapterCount || bookData.total_chapters || 0,
                                    category: bookData.category || bookData.categoryName || null,
                                    tags: bookData.tags || [],
                                    language: "id" // Assume Indonesian if from GoodReels Indonesia
                                };

                                capturedData.dramas[bookId].metadata = metadata;
                                capturedData.dramas[bookId].title = metadata.title;

                                if (metadata.cover && !capturedData.dramas[bookId].cover) {
                                    capturedData.dramas[bookId].cover = metadata.cover;
                                }

                                console.log("\n📖 [METADATA CAPTURED] " + metadata.title);
                                console.log("   Book ID: " + bookId);
                                if (metadata.description && metadata.description.length > 0) {
                                    var shortDesc = metadata.description.substring(0, 60);
                                    console.log("   Desc: " + shortDesc + "...");
                                }

                                updateStats();
                            }
                        }

                        // ===== CHAPTER/EPISODE LIST API =====
                        if ((url.indexOf("/chapter") !== -1 || url.indexOf("/episode") !== -1) && jsonData.data) {
                            var chapters = jsonData.data;
                            if (Array.isArray(chapters) && chapters.length > 0) {
                                var firstChapter = chapters[0];
                                var bookId = firstChapter.bookId || firstChapter.book_id;

                                if (bookId && capturedData.dramas[bookId.toString()]) {
                                    console.log("\n📚 [CHAPTER LIST] Found " + chapters.length + " chapters for drama " + bookId);

                                    // Store chapter metadata
                                    for (var j = 0; j < chapters.length; j++) {
                                        var ch = chapters[j];
                                        var chId = (ch.id || ch.chapterId || ch.chapter_id).toString();

                                        if (capturedData.dramas[bookId.toString()].episodes[chId]) {
                                            capturedData.dramas[bookId.toString()].episodes[chId].metadata = {
                                                title: ch.title || ch.name || "Episode " + (j + 1),
                                                order: ch.order || ch.chapterOrder || (j + 1),
                                                isFree: ch.isFree || ch.is_free || false
                                            };
                                        }
                                    }
                                }
                            }
                        }

                    } catch (parseError) {
                        // Not JSON or parse error, ignore
                    }
                } catch (e) {
                    // Error reading response body, ignore
                }
            }

            return response;
        };
    });

    console.log("[✓] Hooking complete!");
    console.log("\n📱 Now browse dramas in the app");
    console.log("📊 Type: status()        - Show capture statistics");
    console.log("📋 Type: list()          - List all captured dramas");
    console.log("💾 Type: exportData()    - Export JSON with full metadata\n");
});

// Export functions to Frida console
rpc.exports = {
    status: function () {
        printStatus();
        return "Status printed above";
    },

    list: function () {
        var output = "\n" + "=".repeat(60) + "\n";
        output += "CAPTURED DRAMAS\n";
        output += "=".repeat(60) + "\n\n";

        var dramaIds = Object.keys(capturedData.dramas);
        if (dramaIds.length === 0) {
            output += "No dramas captured yet.\n";
        } else {
            for (var i = 0; i < dramaIds.length; i++) {
                var drama = capturedData.dramas[dramaIds[i]];
                var episodeCount = Object.keys(drama.episodes).length;
                var hasMetadata = drama.metadata ? "✓" : "✗";

                output += (i + 1) + ". " + drama.title + "\n";
                output += "   ID: " + drama.bookId + " | Episodes: " + episodeCount + " | Metadata: " + hasMetadata + "\n";

                if (drama.metadata && drama.metadata.description) {
                    var desc = drama.metadata.description.substring(0, 80);
                    output += "   " + desc + "...\n";
                }
                output += "\n";
            }
        }

        output += "=".repeat(60) + "\n";
        console.log(output);
        return "List printed above";
    },

    exportData: function () {
        capturedData.lastUpdate = new Date().toISOString();
        updateStats();

        console.log("\n" + "=".repeat(60));
        console.log("COPY THE JSON BELOW AND SAVE TO: captured-episodes.json");
        console.log("=".repeat(60));
        console.log(JSON.stringify(capturedData, null, 2));
        console.log("=".repeat(60) + "\n");

        return "JSON exported above. Copy and save to captured-episodes.json";
    }
};
