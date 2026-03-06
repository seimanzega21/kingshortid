/**
 * Frida Auto-Save Metadata Capture Script v4
 * 
 * KEY IMPROVEMENTS:
 * ✅ Progressive auto-save after each drama
 * ✅ Crash recovery - data saved to device
 * ✅ Better error handling
 * 
 * Captures:
 * - Video URLs (from CDN requests)
 * - Cover images  
 * - Drama metadata (title, description, etc.) from API responses
 * - Episode metadata (title, order, etc.)
 * 
 * Usage:
 * 1. frida -U -f com.newreading.goodreels -l frida\capture-metadata-autosave.js
 * 2. Browse dramas in the app
 * 3. Data auto-saves to /sdcard/goodshort_capture.json
 * 4. Type: status() to check progress
 * 5. Type: pull() to get adb command to copy file
 */

console.log("\n" + "=".repeat(70));
console.log("🚀 GoodShort Auto-Save Metadata Collector v4");
console.log("📊 Progressive Auto-Save - No Data Loss!");
console.log("=".repeat(70) + "\n");

var SAVE_PATH = "/sdcard/goodshort_capture.json";

// Store captured data
var capturedData = {
    session: {
        startTime: new Date().toISOString(),
        lastSave: null,
        version: "4.0-autosave"
    },
    dramas: {},
    stats: {
        totalDramas: 0,
        totalEpisodes: 0,
        dramasWithMetadata: 0,
        autoSaveCount: 0
    }
};

// Auto-save function
function autoSave() {
    try {
        var File = Java.use("java.io.File");
        var FileWriter = Java.use("java.io.FileWriter");

        updateStats();
        capturedData.session.lastSave = new Date().toISOString();

        var json = JSON.stringify(capturedData, null, 2);
        var file = File.$new(SAVE_PATH);
        var writer = FileWriter.$new(file);
        writer.write(json);
        writer.close();

        capturedData.stats.autoSaveCount++;

        console.log("💾 [AUTO-SAVED #" + capturedData.stats.autoSaveCount + "] " + SAVE_PATH);

        return true;
    } catch (e) {
        console.error("❌ Auto-save failed: " + e);
        return false;
    }
}

// Load existing data if available (crash recovery)
function loadExistingData() {
    try {
        var File = Java.use("java.io.File");
        var FileReader = Java.use("java.io.FileReader");
        var BufferedReader = Java.use("java.io.BufferedReader");

        var file = File.$new(SAVE_PATH);
        if (file.exists()) {
            var reader = BufferedReader.$new(FileReader.$new(file));
            var content = "";
            var line;

            while ((line = reader.readLine()) !== null) {
                content += line;
            }
            reader.close();

            if (content.length > 0) {
                var loaded = JSON.parse(content);
                capturedData.dramas = loaded.dramas || {};

                console.log("♻️  [RECOVERY] Loaded " + Object.keys(capturedData.dramas).length + " dramas from previous session");
                return true;
            }
        }
    } catch (e) {
        console.log("ℹ️  No previous data found - starting fresh");
    }
    return false;
}

// Parse video URL
function parseVideoUrl(url) {
    var match = url.match(/\/mts\/books\/(\d+)\/(\d+)\/(\d+)\/([a-z0-9]+)\/(\d+p)\/([a-z0-9]+)_\d+p[_.]*/i);
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
    if (url.indexOf("acf.goodreels.com/videobook") !== -1 || url.indexOf("cover") !== -1) {
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
        var drama = capturedData.dramas[d];
        capturedData.stats.totalEpisodes += Object.keys(drama.episodes || {}).length;
        if (drama.metadata && drama.metadata.title) {
            capturedData.stats.dramasWithMetadata++;
        }
    }
}

// Initialize drama entry
function initDrama(bookId) {
    if (!capturedData.dramas[bookId]) {
        capturedData.dramas[bookId] = {
            bookId: bookId,
            episodes: {},
            covers: [],
            metadata: null,
            capturedAt: new Date().toISOString()
        };
        return true;
    }
    return false;
}

Java.perform(function () {
    console.log("[*] Installing hooks...\n");

    // Try to recover previous session
    loadExistingData();

    var RealInterceptorChain = Java.use("okhttp3.internal.http.RealInterceptorChain");
    var ResponseBody = Java.use("okhttp3.ResponseBody");

    var proceedMethod = RealInterceptorChain.proceed.overload('okhttp3.Request');

    proceedMethod.implementation = function (request) {
        var url = request.url().toString();
        var response = this.proceed(request);
        var shouldSave = false;

        try {
            // VIDEO URLs
            if (url.indexOf("/mts/books/") !== -1) {
                var parsed = parseVideoUrl(url);
                if (parsed) {
                    var isNew = initDrama(parsed.bookId);

                    if (!capturedData.dramas[parsed.bookId].episodes[parsed.chapterId]) {
                        capturedData.dramas[parsed.bookId].episodes[parsed.chapterId] = {
                            chapterId: parsed.chapterId,
                            videoUrl: url,
                            resolution: parsed.resolution,
                            token: parsed.token
                        };

                        if (isNew) {
                            console.log("\n🎬 [NEW DRAMA] Book ID: " + parsed.bookId);
                        }
                        console.log("   📺 Episode " + Object.keys(capturedData.dramas[parsed.bookId].episodes).length + " captured (Chapter: " + parsed.chapterId + ")");

                        shouldSave = true;
                    }
                }
            }

            // COVER URLs
            if ((url.indexOf("acf.goodreels.com/videobook") !== -1 || url.indexOf("cover") !== -1)) {
                var coverUrl = parseCoverUrl(url);
                if (coverUrl) {
                    var bookIdMatch = url.match(/\/(\d{11,})\//);
                    if (bookIdMatch) {
                        var bookId = bookIdMatch[1];
                        initDrama(bookId);

                        if (capturedData.dramas[bookId].covers.indexOf(coverUrl) === -1) {
                            capturedData.dramas[bookId].covers.push(coverUrl);
                            console.log("   🖼️  Cover captured for drama " + bookId);
                            shouldSave = true;
                        }
                    }
                }
            }

            // API RESPONSES (Metadata)
            if (url.indexOf("api-akm.goodreels.com") !== -1 || url.indexOf("hwycclientreels") !== -1) {
                try {
                    var body = response.body();
                    if (body) {
                        var bodyStr = body.string();

                        if (bodyStr && bodyStr.length > 0) {
                            // Rebuild response
                            var mediaType = body.contentType();
                            var newBody = ResponseBody.create(mediaType, bodyStr);
                            response = response.newBuilder().body(newBody).build();

                            try {
                                var json = JSON.parse(bodyStr);

                                // Book detail response
                                if (json.data && json.data.id && !Array.isArray(json.data)) {
                                    var book = json.data;
                                    var bookId = book.id.toString();

                                    initDrama(bookId);

                                    capturedData.dramas[bookId].metadata = {
                                        title: book.title || book.name || null,
                                        description: book.description || book.intro || null,
                                        genre: book.category || book.categoryName || null,
                                        author: book.author || null,
                                        tags: book.tags || [],
                                        totalChapters: book.totalChapter || 0,
                                        views: book.viewCount || 0,
                                        rating: book.rating || null,
                                        language: book.language || "id"
                                    };

                                    console.log("\n📚 [METADATA] " + (capturedData.dramas[bookId].metadata.title || "Untitled"));
                                    console.log("   📖 Genre: " + (capturedData.dramas[bookId].metadata.genre || "N/A"));
                                    console.log("   📊 Chapters: " + capturedData.dramas[bookId].metadata.totalChapters);

                                    shouldSave = true;
                                }

                                // Chapter list response
                                if (json.data && Array.isArray(json.data) && json.data.length > 0) {
                                    var firstChapter = json.data[0];
                                    if (firstChapter.bookId) {
                                        var bookId = firstChapter.bookId.toString();
                                        initDrama(bookId);

                                        json.data.forEach(function (ch) {
                                            if (!capturedData.dramas[bookId].episodes[ch.id]) {
                                                capturedData.dramas[bookId].episodes[ch.id] = {
                                                    chapterId: ch.id.toString(),
                                                    title: ch.title || null,
                                                    order: ch.chapterOrder || ch.order || 0,
                                                    isFree: ch.isFree !== false
                                                };
                                            }
                                        });

                                        console.log("\n📋 [EPISODE LIST] " + json.data.length + " chapters for drama " + bookId);
                                        shouldSave = true;
                                    }
                                }

                            } catch (parseErr) {
                                // Not JSON or parse error
                            }
                        }
                    }
                } catch (bodyErr) {
                    // Body read error
                }
            }

        } catch (e) {
            console.error("⚠️  Hook error: " + e);
        }

        // AUTO-SAVE when new data captured
        if (shouldSave) {
            autoSave();
        }

        return response;
    };

    console.log("[✓] Hooking complete!\n");
    console.log("📱 Now browse dramas in the app");
    console.log("📊 Type: status()        - Show capture statistics");
    console.log("📋 Type: list()          - List all captured dramas");
    console.log("💾 Type: save()          - Force save now");
    console.log("📥 Type: pull()          - Get adb command to pull data");
    console.log("");
});

// RPC exports
rpc.exports = {
    status: function () {
        updateStats();

        console.log("\n╔" + "═".repeat(68) + "╗");
        console.log("║" + " ".repeat(22) + "📊 CAPTURE STATUS" + " ".repeat(28) + "║");
        console.log("╠" + "═".repeat(68) + "╣");
        console.log("║  Total Dramas:      " + capturedData.stats.totalDramas.toString().padEnd(10) + " ".repeat(37) + "║");
        console.log("║  With Metadata:     " + capturedData.stats.dramasWithMetadata.toString().padEnd(10) + " ".repeat(37) + "║");
        console.log("║  Total Episodes:    " + capturedData.stats.totalEpisodes.toString().padEnd(10) + " ".repeat(37) + "║");
        console.log("║  Auto-Saves:        " + capturedData.stats.autoSaveCount.toString().padEnd(10) + " ".repeat(37) + "║");
        console.log("║  Last Save:         " + (capturedData.session.lastSave ? capturedData.session.lastSave.substring(11, 19) : "Never").padEnd(47) + "║");
        console.log("╚" + "═".repeat(68) + "╝\n");

        return capturedData.stats;
    },

    list: function () {
        console.log("\n" + "=".repeat(70));
        console.log("CAPTURED DRAMAS (" + capturedData.stats.totalDramas + " total)");
        console.log("=".repeat(70) + "\n");

        var ids = Object.keys(capturedData.dramas);
        for (var i = 0; i < ids.length; i++) {
            var drama = capturedData.dramas[ids[i]];
            var title = drama.metadata && drama.metadata.title ? drama.metadata.title : "Drama " + ids[i];
            var epCount = Object.keys(drama.episodes).length;
            var coverCount = drama.covers.length;

            console.log((i + 1) + ". " + title);
            console.log("   ID: " + ids[i]);
            console.log("   Episodes: " + epCount + " | Covers: " + coverCount);
            console.log("   Metadata: " + (drama.metadata ? "✅" : "❌"));
            console.log("");
        }

        return ids.length;
    },

    save: function () {
        console.log("\n💾 Force saving...");
        return autoSave() ? "✅ Saved" : "❌ Failed";
    },

    pull: function () {
        console.log("\n📥 To pull data from device:");
        console.log("\n   adb pull " + SAVE_PATH + " .\n");
        console.log("Then process with:");
        console.log("   python production_processor.py\n");
        return SAVE_PATH;
    },

    exportData: function () {
        updateStats();
        console.log("\n" + "=".repeat(70));
        console.log("EXPORT DATA");
        console.log("=".repeat(70));
        console.log(JSON.stringify(capturedData, null, 2));
        console.log("=".repeat(70) + "\n");
        return capturedData;
    }
};

// Global shortcuts
globalThis.status = function () { return rpc.exports.status(); };
globalThis.list = function () { return rpc.exports.list(); };
globalThis.save = function () { return rpc.exports.save(); };
globalThis.pull = function () { return rpc.exports.pull(); };
globalThis.exportData = function () { return rpc.exports.exportData(); };
