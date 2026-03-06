/**
 * Enhanced Metadata Capture Script v4
 * 
 * GOAL: Complete capture of drama metadata including:
 * - Cover images (high quality)
 * - Title, description, genre, author
 * - Episode list with metadata
 * - Auto-save to file system
 * 
 * Usage:
 * 1. Run emulator with GoodReels app
 * 2. frida -U -f com.newreading.goodreels -l frida\capture-metadata-enhanced.js --no-pause
 * 3. Browse Indonesian dramas in the app
 * 4. Data auto-saves to: scraped_data/metadata_capture/
 * 
 * Commands:
 * - status() : Show capture statistics
 * - list()   : List all captured dramas
 * - save()   : Force save to JSON files
 * - export() : Export JSON to console
 */

console.log("\n" + "=".repeat(70));
console.log("📚 GoodShort ENHANCED Metadata Collector v4");
console.log("🎯 Focus: Indonesian Dramas - Full Metadata + Covers");
console.log("=".repeat(70) + "\n");

// Enhanced data store
var capturedData = {
    captureSession: {
        startTime: new Date().toISOString(),
        lastUpdate: null,
        version: "4.0"
    },
    dramas: {},
    covers: {},
    apiResponses: [],
    stats: {
        totalDramas: 0,
        totalEpisodes: 0,
        dramasWithFullMetadata: 0,
        coversCapture: 0
    }
};

// Track book IDs we need metadata for
var pendingMetadata = new Set();

// CDN Domain patterns
var CDN_PATTERNS = {
    video: "v2-akm.goodreels.com/mts/books",
    cover: "acf.goodreels.com/videobook",
    api: "api-akm.goodreels.com"
};

// Parse video URL to extract identifiers
function parseVideoUrl(url) {
    // Pattern: /mts/books/{suffix}/{bookId}/{chapterId}/{token}/{resolution}/{videoId}_{resolution}_{segment}.ts
    var match = url.match(/\/mts\/books\/(\d+)\/(\d+)\/(\d+)\/([a-z0-9]+)\/(\d+p)\/([a-z0-9]+)_\d+p[_.]*/i);
    if (match) {
        return {
            bookSuffix: match[1],
            bookId: match[2],
            chapterId: match[3],
            token: match[4],
            resolution: match[5],
            videoId: match[6]
        };
    }
    return null;
}

// Parse cover URL to extract book ID
function parseCoverUrl(url) {
    // Pattern: /videobook/{bookId}/{something}/cover-{size}.jpg
    var match = url.match(/\/videobook\/(\d+)\/[^\/]+\/cover-([^.]+)\./i);
    if (match) {
        return {
            bookId: match[1],
            size: match[2],
            fullUrl: url.split('?')[0]
        };
    }
    return null;
}

// Update statistics
function updateStats() {
    var dramaIds = Object.keys(capturedData.dramas);
    capturedData.stats.totalDramas = dramaIds.length;
    capturedData.stats.totalEpisodes = 0;
    capturedData.stats.dramasWithFullMetadata = 0;
    capturedData.stats.coversCapture = Object.keys(capturedData.covers).length;

    for (var i = 0; i < dramaIds.length; i++) {
        var drama = capturedData.dramas[dramaIds[i]];
        capturedData.stats.totalEpisodes += Object.keys(drama.episodes || {}).length;

        // Check if has full metadata
        if (drama.metadata && drama.metadata.title && drama.metadata.description && drama.cover) {
            capturedData.stats.dramasWithFullMetadata++;
        }
    }
}

// Print detailed status
function printStatus() {
    updateStats();
    var s = capturedData.stats;

    console.log("\n╔══════════════════════════════════════════════════════════════════╗");
    console.log("║                     📊 CAPTURE STATUS                              ║");
    console.log("╠══════════════════════════════════════════════════════════════════╣");
    console.log("║  Dramas Captured:        " + s.totalDramas.toString().padEnd(10) + "                              ║");
    console.log("║  Episodes Captured:      " + s.totalEpisodes.toString().padEnd(10) + "                              ║");
    console.log("║  With Full Metadata:     " + s.dramasWithFullMetadata.toString().padEnd(10) + "                              ║");
    console.log("║  Covers Captured:        " + s.coversCapture.toString().padEnd(10) + "                              ║");
    console.log("║  API Responses Logged:   " + capturedData.apiResponses.length.toString().padEnd(10) + "                              ║");
    console.log("╚══════════════════════════════════════════════════════════════════╝\n");

    // List dramas needing metadata
    if (pendingMetadata.size > 0) {
        console.log("⏳ Dramas needing metadata: " + Array.from(pendingMetadata).join(", "));
    }
}

// Initialize drama entry
function initDrama(bookId) {
    if (!capturedData.dramas[bookId]) {
        capturedData.dramas[bookId] = {
            bookId: bookId,
            title: null,
            cover: null,
            coverHQ: null,
            metadata: null,
            episodes: {},
            chapterList: null,
            rawApiResponse: null,
            capturedAt: new Date().toISOString()
        };
        pendingMetadata.add(bookId);
        console.log("\n🆕 [NEW DRAMA] Book ID: " + bookId);
        return true;
    }
    return false;
}

// Main hook
Java.perform(function () {
    console.log("[*] Initializing hooks...\n");

    // OkHttp3 Interceptor - catches all HTTP traffic
    var RealInterceptorChain = Java.use("okhttp3.internal.http.RealInterceptorChain");
    var ResponseBody = Java.use("okhttp3.ResponseBody");

    RealInterceptorChain.proceed.overloads.forEach(function (method) {
        method.implementation = function () {
            var request = this.request();
            var url = request.url().toString();
            var response = null;

            // Execute original request
            if (arguments.length === 0) {
                response = this.proceed();
            } else {
                response = this.proceed(arguments[0]);
            }

            capturedData.captureSession.lastUpdate = new Date().toISOString();

            // =================== VIDEO CDN ===================
            if (url.indexOf(CDN_PATTERNS.video) !== -1) {
                var videoParsed = parseVideoUrl(url);
                if (videoParsed) {
                    var bookId = videoParsed.bookId;
                    var isNew = initDrama(bookId);

                    var chapterId = videoParsed.chapterId;
                    if (!capturedData.dramas[bookId].episodes[chapterId]) {
                        capturedData.dramas[bookId].episodes[chapterId] = {
                            chapterId: chapterId,
                            token: videoParsed.token,
                            videoId: videoParsed.videoId,
                            resolution: videoParsed.resolution,
                            capturedAt: new Date().toISOString()
                        };

                        var epCount = Object.keys(capturedData.dramas[bookId].episodes).length;
                        console.log("   📺 Episode " + epCount + " (Chapter: " + chapterId + ", " + videoParsed.resolution + ")");
                    }
                }
            }

            // =================== COVER CDN ===================
            if (url.indexOf(CDN_PATTERNS.cover) !== -1 && url.indexOf("cover-") !== -1) {
                var coverParsed = parseCoverUrl(url);
                if (coverParsed) {
                    var bookId = coverParsed.bookId;

                    // Store all cover sizes
                    if (!capturedData.covers[bookId]) {
                        capturedData.covers[bookId] = {};
                    }
                    capturedData.covers[bookId][coverParsed.size] = coverParsed.fullUrl;

                    // Assign to drama
                    if (capturedData.dramas[bookId]) {
                        capturedData.dramas[bookId].cover = coverParsed.fullUrl;

                        // Prefer HQ version
                        if (coverParsed.size.indexOf("720") !== -1 || coverParsed.size.indexOf("1080") !== -1) {
                            capturedData.dramas[bookId].coverHQ = coverParsed.fullUrl;
                        }

                        console.log("   🖼️  Cover (" + coverParsed.size + ") for drama " + bookId);
                    }
                }
            }

            // =================== API RESPONSES ===================
            if (url.indexOf(CDN_PATTERNS.api) !== -1 && response) {
                try {
                    var responseBody = response.body();
                    if (responseBody && responseBody !== null) {
                        var bodyString = responseBody.string();

                        if (bodyString && bodyString.length > 0) {
                            // Rebuild response body
                            var mediaType = responseBody.contentType();
                            var newBody = ResponseBody.create(mediaType, bodyString);
                            response = response.newBuilder().body(newBody).build();

                            // Try parse JSON
                            try {
                                var jsonData = JSON.parse(bodyString);

                                // Log API response summary
                                var responseInfo = {
                                    url: url,
                                    timestamp: new Date().toISOString(),
                                    hasData: !!jsonData.data,
                                    dataType: jsonData.data ? (Array.isArray(jsonData.data) ? "array" : "object") : null
                                };
                                capturedData.apiResponses.push(responseInfo);

                                // ===== BOOK/DRAMA DETAIL =====
                                if (url.indexOf("/book") !== -1 && jsonData.data && !Array.isArray(jsonData.data)) {
                                    var bookData = jsonData.data;
                                    var bookId = (bookData.id || bookData.bookId || bookData.book_id || "").toString();

                                    if (bookId && bookId.length >= 10) {
                                        initDrama(bookId);

                                        // Extract full metadata
                                        var metadata = {
                                            title: bookData.title || bookData.name || bookData.bookName,
                                            description: bookData.description || bookData.desc || bookData.synopsis || bookData.intro,
                                            author: bookData.author || bookData.authorName || bookData.writer,
                                            category: bookData.category || bookData.categoryName || bookData.genre,
                                            tags: bookData.tags || bookData.tagList || [],
                                            totalChapters: bookData.totalChapter || bookData.chapterCount || bookData.episodeCount || 0,
                                            views: bookData.viewCount || bookData.views || 0,
                                            likes: bookData.likeCount || bookData.likes || 0,
                                            rating: bookData.rating || bookData.score || null,
                                            status: bookData.status || bookData.bookStatus || null,
                                            updateTime: bookData.updateTime || bookData.lastUpdateTime || null,
                                            language: bookData.language || "id"
                                        };

                                        // Update drama with metadata
                                        capturedData.dramas[bookId].metadata = metadata;
                                        capturedData.dramas[bookId].title = metadata.title;
                                        capturedData.dramas[bookId].rawApiResponse = bookData;

                                        // Get cover from API if available
                                        if (bookData.cover || bookData.coverUrl || bookData.image) {
                                            var apiCover = bookData.cover || bookData.coverUrl || bookData.image;
                                            if (!capturedData.dramas[bookId].cover) {
                                                capturedData.dramas[bookId].cover = apiCover;
                                            }
                                        }

                                        // Remove from pending
                                        pendingMetadata.delete(bookId);

                                        console.log("\n📖 [METADATA CAPTURED] " + (metadata.title || "Unknown"));
                                        console.log("   📝 ID: " + bookId);
                                        console.log("   📂 Category: " + (metadata.category || "N/A"));
                                        console.log("   📺 Chapters: " + (metadata.totalChapters || "?"));
                                        if (metadata.description) {
                                            console.log("   📄 Desc: " + metadata.description.substring(0, 50) + "...");
                                        }

                                        updateStats();
                                    }
                                }

                                // ===== CHAPTER/EPISODE LIST =====
                                if ((url.indexOf("/chapter") !== -1 || url.indexOf("/episode") !== -1) && jsonData.data) {
                                    var chapterData = jsonData.data;
                                    var chapters = Array.isArray(chapterData) ? chapterData : (chapterData.list || chapterData.chapters || []);

                                    if (chapters.length > 0) {
                                        var firstChapter = chapters[0];
                                        var bookId = (firstChapter.bookId || firstChapter.book_id || "").toString();

                                        if (bookId && capturedData.dramas[bookId]) {
                                            capturedData.dramas[bookId].chapterList = chapters.map(function (ch, idx) {
                                                return {
                                                    id: (ch.id || ch.chapterId || ch.chapter_id).toString(),
                                                    title: ch.title || ch.name || ("Episode " + (idx + 1)),
                                                    order: ch.order || ch.chapterOrder || (idx + 1),
                                                    isFree: ch.isFree !== false && ch.is_free !== false,
                                                    duration: ch.duration || ch.time || null
                                                };
                                            });

                                            console.log("\n📚 [CHAPTER LIST] " + chapters.length + " chapters for drama " + bookId);
                                        }
                                    }
                                }

                                // ===== HOME/LIST RESPONSES (Bulk drama data) =====
                                if (jsonData.data && Array.isArray(jsonData.data) && jsonData.data.length > 0) {
                                    var items = jsonData.data;
                                    var bookItem = items[0];

                                    // Check if it's book list
                                    if (bookItem.bookId || bookItem.id) {
                                        console.log("\n📋 [BULK LIST] Processing " + items.length + " items...");

                                        for (var i = 0; i < items.length; i++) {
                                            var item = items[i];
                                            var itemBookId = (item.bookId || item.id || "").toString();

                                            if (itemBookId.length >= 10) {
                                                initDrama(itemBookId);

                                                // Partial metadata from list
                                                if (!capturedData.dramas[itemBookId].metadata) {
                                                    capturedData.dramas[itemBookId].metadata = {
                                                        title: item.title || item.name || item.bookName,
                                                        description: item.description || item.desc || item.intro,
                                                        category: item.category || item.categoryName,
                                                        totalChapters: item.totalChapter || item.chapterCount || 0
                                                    };
                                                    capturedData.dramas[itemBookId].title = item.title || item.name;
                                                }

                                                // Cover from list
                                                if (item.cover && !capturedData.dramas[itemBookId].cover) {
                                                    capturedData.dramas[itemBookId].cover = item.cover;
                                                }
                                            }
                                        }

                                        updateStats();
                                        console.log("   ✅ Processed " + items.length + " dramas from list");
                                    }
                                }
                            }

                            } catch (parseError) {
                            // Not JSON, skip
                        }
                    }
                }
                } catch (e) {
                // Response read error, skip
            }
        }

        return response;
    };
});

console.log("[✓] All hooks installed!\n");
console.log("📱 Browse dramas in the GoodReels app now.");
console.log("📊 Type: status() - Show statistics");
console.log("📋 Type: list()   - List captured dramas");
console.log("💾 Type: save()   - Force save to console (copy to file)");
console.log("");
});

// RPC Exports
rpc.exports = {
    status: function () {
        printStatus();
        return capturedData.stats;
    },

    list: function () {
        updateStats();
        var output = "\n" + "=".repeat(70) + "\n";
        output += "CAPTURED DRAMAS (" + capturedData.stats.totalDramas + " total)\n";
        output += "=".repeat(70) + "\n\n";

        var dramaIds = Object.keys(capturedData.dramas);
        if (dramaIds.length === 0) {
            output += "No dramas captured yet. Browse the app!\n";
        } else {
            for (var i = 0; i < dramaIds.length; i++) {
                var drama = capturedData.dramas[dramaIds[i]];
                var episodeCount = Object.keys(drama.episodes || {}).length;
                var hasMeta = drama.metadata && drama.metadata.title ? "✓" : "✗";
                var hasCover = drama.cover ? "✓" : "✗";

                output += (i + 1) + ". " + (drama.title || "Drama " + drama.bookId) + "\n";
                output += "   ID: " + drama.bookId + " | Eps: " + episodeCount;
                output += " | Meta: " + hasMeta + " | Cover: " + hasCover + "\n";

                if (drama.metadata && drama.metadata.category) {
                    output += "   Category: " + drama.metadata.category + "\n";
                }
                if (drama.metadata && drama.metadata.description) {
                    output += "   Desc: " + drama.metadata.description.substring(0, 60) + "...\n";
                }
                if (drama.cover) {
                    output += "   Cover: " + drama.cover.substring(0, 50) + "...\n";
                }
                output += "\n";
            }
        }

        output += "=".repeat(70) + "\n";
        console.log(output);
        return "Listed " + capturedData.stats.totalDramas + " dramas";
    },

    save: function () {
        updateStats();
        capturedData.captureSession.lastUpdate = new Date().toISOString();

        console.log("\n" + "=".repeat(70));
        console.log("💾 COMPLETE CAPTURE DATA - Save as: metadata_complete.json");
        console.log("=".repeat(70));
        console.log(JSON.stringify(capturedData, null, 2));
        console.log("=".repeat(70) + "\n");

        return "Data exported to console. Copy and save to file.";
    },

    getData: function () {
        updateStats();
        return capturedData;
    }
};

// Global shortcuts
globalThis.status = function () { return rpc.exports.status(); };
globalThis.list = function () { return rpc.exports.list(); };
globalThis.save = function () { return rpc.exports.save(); };
globalThis.exportData = function () { return rpc.exports.save(); };
