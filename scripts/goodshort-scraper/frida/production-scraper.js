/**
 * GoodShort Production Metadata Scraper v5
 * 
 * Complete solution that captures:
 * - Real drama titles
 * - Real cover image URLs (high quality)
 * - Full metadata (description, genre, author, etc)
 * - Episode lists with metadata
 * - Video URLs for HLS streaming
 * 
 * Auto-saves all data for production use
 * 
 * Usage:
 *   frida -U -f com.newreading.goodreels -l frida/production-scraper.js
 */

console.log("\n" + "=".repeat(80));
console.log("🚀 GoodShort PRODUCTION Metadata Scraper v5");
console.log("📊 Complete Metadata + Real Covers + Video URLs");
console.log("=".repeat(80) + "\n");

// Production data store
var productionData = {
    session: {
        startTime: new Date().toISOString(),
        version: "5.0-production",
        lastUpdate: null
    },
    dramas: {},
    covers: {},
    rawResponses: [],
    stats: {
        dramasTotal: 0,
        dramasComplete: 0,
        coversFound: 0,
        episodesTotal: 0
    }
};

// Save path
var SAVE_PATH = "/sdcard/goodshort_production_data.json";

function saveToDisk() {
    try {
        var File = Java.use("java.io.File");
        var FileWriter = Java.use("java.io.FileWriter");

        var json = JSON.stringify(productionData, null, 2);
        var file = File.$new(SAVE_PATH);
        var writer = FileWriter.$new(file);
        writer.write(json);
        writer.close();

        console.log("\n💾 [AUTO-SAVED] " + SAVE_PATH);
        console.log("   📋 Copy: adb pull " + SAVE_PATH + " .\n");

        return true;
    } catch (e) {
        console.error("❌ Save failed: " + e);
        return false;
    }
}

function updateStats() {
    var ids = Object.keys(productionData.dramas);
    productionData.stats.dramasTotal = ids.length;
    productionData.stats.coversFound = Object.keys(productionData.covers).length;
    productionData.stats.dramasComplete = 0;
    productionData.stats.episodesTotal = 0;

    for (var i = 0; i < ids.length; i++) {
        var drama = productionData.dramas[ids[i]];

        if (drama.title && drama.cover && drama.description) {
            productionData.stats.dramasComplete++;
        }

        if (drama.episodes) {
            productionData.stats.episodesTotal += drama.episodes.length;
        }
    }
}

function initDrama(bookId) {
    if (!productionData.dramas[bookId]) {
        productionData.dramas[bookId] = {
            bookId: bookId,
            title: null,
            originalTitle: null,
            cover: null,
            coverHQ: null,
            coverOptions: {},
            description: null,
            genre: null,
            category: null,
            author: null,
            tags: [],
            totalEpisodes: 0,
            episodes: [],
            metadata: {},
            videoUrls: [],
            capturedAt: new Date().toISOString()
        };

        console.log("\n🆕 [NEW] Drama " + bookId);
        return true;
    }
    return false;
}

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

function parseCoverUrl(url) {
    var match = url.match(/\/videobook\/(\d+)\/[^\/]+\/(cover-)?([^.?]+)\./i);
    if (match) {
        return {
            bookId: match[1],
            size: match[3],
            fullUrl: url.split('?')[0]
        };
    }
    return null;
}

Java.perform(function () {
    console.log("[*] Installing production hooks...\n");

    var RealInterceptorChain = Java.use("okhttp3.internal.http.RealInterceptorChain");
    var ResponseBody = Java.use("okhttp3.ResponseBody");

    RealInterceptorChain.proceed.overload('okhttp3.Request').implementation = function (request) {
        var url = "";
        var response = null;

        try {
            // Try to get URL - handle potential TypeError
            var urlObj = request.url();
            url = urlObj ? urlObj.toString() : "";
        } catch (e) {
            // Silent fail - URL extraction failed, proceed with original request
            console.log("[!] URL extraction failed (TypeError), proceeding with original request: " + e);
            return this.proceed(request);
        }

        try {
            response = this.proceed(request);
        } catch (e) {
            console.log("[!] Error proceeding request: " + e);
            throw e;
        }

        productionData.session.lastUpdate = new Date().toISOString();

        // VIDEO URLs
        if (url.indexOf("/mts/books/") !== -1) {
            var parsed = parseVideoUrl(url);
            if (parsed) {
                initDrama(parsed.bookId);

                var drama = productionData.dramas[parsed.bookId];
                drama.videoUrls.push({
                    chapterId: parsed.chapterId,
                    url: url,
                    resolution: parsed.resolution,
                    token: parsed.token
                });

                console.log("   📹 Video: Chapter " + parsed.chapterId + " (" + parsed.resolution + ")");
            }
        }

        // COVER CDN
        if (url.indexOf("/videobook/") !== -1 && url.indexOf("cover") !== -1) {
            var coverParsed = parseCoverUrl(url);
            if (coverParsed) {
                var opts = productionData.covers[coverParsed.bookId] || {};
                opts[coverParsed.size] = url; // Use coverParsed.size here
                productionData.covers[coverParsed.bookId] = opts;

                initDrama(coverParsed.bookId);
                var drama = productionData.dramas[coverParsed.bookId];

                // Update cover - prefer higher quality
                if (!drama.coverHQ && url.indexOf("-720") !== -1) {
                    drama.coverHQ = url;
                }
                if (!drama.cover) {
                    drama.cover = url;
                }
                drama.coverOptions = opts;
            }
        }

        // API RESPONSES for metadata
        if (url.indexOf("api-akm.goodreels.com") !== -1 || url.indexOf("hwycclientreels") !== -1) {
            try {
                // Store raw response
                productionData.rawResponses.push({
                    url: url,
                    timestamp: new Date().toISOString(),
                    data: json
                });

                // BOOK DETAIL API
                if (url.indexOf("/book") !== -1 && json.data && !Array.isArray(json.data)) {
                    var book = json.data;
                    var bookId = (book.id || book.bookId || book.book_id || "").toString();

                    if (bookId.length >= 10) {
                        initDrama(bookId);
                        var drama = productionData.dramas[bookId];

                        // Extract ALL metadata
                        drama.title = book.title || book.name || book.bookName || null;
                        drama.originalTitle = book.originalTitle || book.original_title || null;
                        drama.description = book.description || book.desc || book.synopsis || book.intro || null;
                        drama.author = book.author || book.authorName || book.writer || null;
                        drama.genre = book.genre || book.category || book.categoryName || null;
                        drama.category = book.category || book.categoryName || null;
                        drama.tags = book.tags || book.tagList || [];
                        drama.totalEpisodes = book.totalChapter || book.chapterCount || book.episodeCount || 0;

                        drama.metadata = {
                            views: book.viewCount || book.views || 0,
                            likes: book.likeCount || book.likes || 0,
                            rating: book.rating || book.score || null,
                            status: book.status || book.bookStatus || null,
                            releaseYear: book.releaseYear || book.year || null,
                            language: book.language || "id",
                            updateTime: book.updateTime || book.lastUpdateTime || null
                        };

                        // Cover from API
                        if (book.cover || book.coverUrl || book.image) {
                            var apiCover = book.cover || book.coverUrl || book.image;
                            if (!drama.cover) {
                                drama.cover = apiCover;
                            }
                        }

                        console.log("\n📚 [COMPLETE METADATA]");
                        console.log("   📖 Title: " + (drama.title || "N/A"));
                        console.log("   🏷️  Genre: " + (drama.genre || "N/A"));
                        console.log("   📝 Desc: " + (drama.description ? drama.description.substring(0, 40) + "..." : "N/A"));
                        console.log("   📊 Episodes: " + drama.totalEpisodes);

                        updateStats();
                        saveToDisk();
                    }
                }

                // CHAPTER LIST API
                if ((url.indexOf("/chapter") !== -1 || url.indexOf("/episode") !== -1) && json.data) {
                    var chapters = Array.isArray(json.data) ? json.data : (json.data.list || json.data.chapters || []);

                    if (chapters.length > 0) {
                        var firstCh = chapters[0];
                        var bookId = (firstCh.bookId || firstCh.book_id || "").toString();

                        if (bookId && productionData.dramas[bookId]) {
                            productionData.dramas[bookId].episodes = chapters.map(function (ch, idx) {
                                return {
                                    id: (ch.id || ch.chapterId || ch.chapter_id || "").toString(),
                                    title: ch.title || ch.name || ("Episode " + (idx + 1)),
                                    order: ch.order || ch.chapterOrder || (idx + 1),
                                    isFree: ch.isFree !== false && ch.is_free !== false,
                                    duration: ch.duration || ch.time || null,
                                    thumbnail: ch.thumbnail || ch.thumb || null
                                };
                            });

                            console.log("\n📋 [EPISODE LIST] " + chapters.length + " episodes (Drama " + bookId + ")");

                            updateStats();
                            saveToDisk();
                        }
                    }
                }

                // BULK LIST (Home/Discover)
                if (json.data && Array.isArray(json.data) && json.data.length > 0) {
                    var items = json.data;
                    var first = items[0];

                    if (first.bookId || first.id) {
                        console.log("\n📦 [BULK LIST] " + items.length + " items");

                        for (var i = 0; i < items.length; i++) {
                            var item = items[i];
                            var itemId = (item.bookId || item.id || "").toString();

                            if (itemId.length >= 10) {
                                initDrama(itemId);
                                var d = productionData.dramas[itemId];

                                if (!d.title) d.title = item.title || item.name || item.bookName;
                                if (!d.description) d.description = item.description || item.desc || item.intro;
                                if (!d.genre) d.genre = item.category || item.categoryName || item.genre;
                                if (!d.cover && item.cover) d.cover = item.cover;
                            }
                        }

                        updateStats();
                        saveToDisk();
                    }
                }

            } catch (parseErr) {
                // Not JSON
            }
        }
    }
} catch (e) {
    // Body read error
}
        }

return response;
    };

console.log("[✓] Production hooks installed!\n");
console.log("📱 Browse dramas now - data auto-saves");
console.log("\n📊 Commands:");
console.log("   status()  - Show statistics");
console.log("   list()    - List all dramas");
console.log("   save()    - Force save");
console.log("   export()  - Export JSON");
console.log("");
});

// RPC Exports
rpc.exports = {
    status: function () {
        updateStats();

        console.log("\n╔" + "═".repeat(78) + "╗");
        console.log("║" + " ".repeat(25) + "📊 PRODUCTION STATUS" + " ".repeat(33) + "║");
        console.log("╠" + "═".repeat(78) + "╣");
        console.log("║  Total Dramas:        " + productionData.stats.dramasTotal.toString().padEnd(10) + " ".repeat(45) + "║");
        console.log("║  Complete Metadata:   " + productionData.stats.dramasComplete.toString().padEnd(10) + " ".repeat(45) + "║");
        console.log("║  Covers Found:        " + productionData.stats.coversFound.toString().padEnd(10) + " ".repeat(45) + "║");
        console.log("║  Total Episodes:      " + productionData.stats.episodesTotal.toString().padEnd(10) + " ".repeat(45) + "║");
        console.log("║  API Responses:       " + productionData.rawResponses.length.toString().padEnd(10) + " ".repeat(45) + "║");
        console.log("╚" + "═".repeat(78) + "╝\n");

        return productionData.stats;
    },

    list: function () {
        updateStats();
        var ids = Object.keys(productionData.dramas);

        console.log("\n" + "=".repeat(80));
        console.log("CAPTURED DRAMAS (" + ids.length + " total)");
        console.log("=".repeat(80) + "\n");

        for (var i = 0; i < ids.length; i++) {
            var d = productionData.dramas[ids[i]];
            var complete = (d.title && d.cover && d.description) ? "✅" : "⏳";

            console.log((i + 1) + ". " + complete + " " + (d.title || ("Drama " + d.bookId)));
            console.log("   ID: " + d.bookId);
            console.log("   Cover: " + (d.cover ? "✅" : "❌"));
            console.log("   Episodes: " + d.episodes.length);
            if (d.genre) console.log("   Genre: " + d.genre);
            console.log("");
        }

        return ids.length;
    },

    save: function () {
        productionData.session.lastUpdate = new Date().toISOString();
        return saveToDisk() ? "✅ Saved" : "❌ Failed";
    },

    export: function () {
        updateStats();
        console.log("\n" + "=".repeat(80));
        console.log("PRODUCTION DATA EXPORT");
        console.log("=".repeat(80));
        console.log(JSON.stringify(productionData, null, 2));
        console.log("=".repeat(80) + "\n");

        return productionData;
    },

    getDrama: function (bookId) {
        return productionData.dramas[bookId] || null;
    }
};

// Global shortcuts
globalThis.status = function () { return rpc.exports.status(); };
globalThis.list = function () { return rpc.exports.list(); };
globalThis.save = function () { return rpc.exports.save(); };
globalThis.export = function () { return rpc.exports.export(); };
