/**
 * ENHANCED VIDEO SEGMENT SAVER - AUTO MODE
 * ==========================================
 * 
 * Enhanced version that auto-detects episodes and saves segments
 * with better organization and real-time stats.
 */

console.log("\n" + "=".repeat(70));
console.log("🎬 ENHANCED VIDEO SEGMENT SAVER - AUTO MODE");
console.log("=".repeat(70) + "\n");

const STORAGE_PATH = "/sdcard/goodshort_segments";
const File = Java.use("java.io.File");
const FileOutputStream = Java.use("java.io.FileOutputStream");

// Create storage
const storageDir = File.$new(STORAGE_PATH);
if (!storageDir.exists()) {
    storageDir.mkdirs();
}

// Stats tracking
let stats = {
    totalEpisodes: 0,
    totalSegments: 0,
    totalBytes: 0,
    currentEpisode: null,
    episodes: {}
};

// Current episode tracking
let currentEpisode = {
    bookId: null,
    episodeId: null,
    segmentCount: 0,
    playlistSaved: false,
    startTime: null
};

function saveToFile(filename, data) {
    try {
        const file = File.$new(STORAGE_PATH + "/" + filename);
        const fos = FileOutputStream.$new(file);

        if (typeof data === 'string') {
            const bytes = Java.use("java.lang.String").$new(data).getBytes();
            fos.write(bytes);
            stats.totalBytes += bytes.length;
        } else {
            fos.write(data);
            stats.totalBytes += data.length;
        }

        fos.close();
        return true;
    } catch (e) {
        return false;
    }
}

function onNewEpisode(episodeId) {
    // Episode changed
    if (currentEpisode.episodeId && currentEpisode.episodeId !== episodeId) {
        const duration = (Date.now() - currentEpisode.startTime) / 1000;
        console.log("\n[✅] Episode " + currentEpisode.episodeId + " COMPLETE:");
        console.log("    Segments: " + currentEpisode.segmentCount);
        console.log("    Duration: " + Math.round(duration) + "s");
        console.log("");

        stats.episodes[currentEpisode.episodeId] = currentEpisode.segmentCount;
        stats.totalEpisodes++;
    }

    // Start new episode
    currentEpisode = {
        bookId: null,
        episodeId: episodeId,
        segmentCount: 0,
        playlistSaved: false,
        startTime: Date.now()
    };

    stats.currentEpisode = episodeId;

    console.log("\n[🎬] NEW EPISODE DETECTED: " + episodeId);
    console.log("    Capturing segments...");
}

// Hook OkHttp3 Response
try {
    const Response = Java.use("okhttp3.Response");
    const ResponseBody = Java.use("okhttp3.ResponseBody");

    Response.body.implementation = function () {
        const response = this.body();
        const request = this.request();
        const url = request.url().toString();

        // Check for HLS content
        if (url.includes(".m3u8")) {
            // Playlist detected
            try {
                const bytes = response.bytes();
                const content = Java.use("java.lang.String").$new(bytes);

                // Extract episode ID
                const match = url.match(/\/(\d+)\/[a-z0-9]+\/720p\//);
                if (match) {
                    const episodeId = match[1];

                    if (!currentEpisode.episodeId || currentEpisode.episodeId !== episodeId) {
                        onNewEpisode(episodeId);
                    }

                    if (!currentEpisode.playlistSaved) {
                        const filename = "episode_" + episodeId + "_playlist.m3u8";
                        if (saveToFile(filename, content)) {
                            currentEpisode.playlistSaved = true;
                            console.log("    📝 Playlist saved");
                        }
                    }
                }

                // Return new response body
                const MediaType = Java.use("okhttp3.MediaType");
                const newBody = ResponseBody.create(
                    response.body().contentType(),
                    bytes
                );
                return newBody;

            } catch (e) {
                // Return original on error
                return response;
            }
        }

        return response;
    };

    console.log("[+] Hooked: okhttp3.Response.body");

} catch (e) {
    console.log("[!] Response hook failed: " + e);
}

// Hook for .ts segments
try {
    const OkHttpClient = Java.use("okhttp3.OkHttpClient");
    const Call = Java.use("okhttp3.Call");

    // Find and hook the internal call execution
    Java.choose("okhttp3.RealCall", {
        onMatch: function (instance) {
            // Hook execute
            instance.execute.implementation = function () {
                const request = this.request();
                const url = request.url().toString();
                const response = this.execute();

                // Check for .ts segment
                if (url.includes(".ts") && url.includes("goodreels.com") && currentEpisode.episodeId) {
                    try {
                        const body = response.body();
                        const bytes = body.bytes();

                        const filename = "episode_" + currentEpisode.episodeId +
                            "_segment_" + String(currentEpisode.segmentCount).padStart(6, '0') + ".ts";

                        if (saveToFile(filename, bytes)) {
                            currentEpisode.segmentCount++;
                            stats.totalSegments++;

                            // Progress every 10 segments
                            if (currentEpisode.segmentCount % 10 === 0) {
                                console.log("    [" + currentEpisode.segmentCount + "] segments...");
                            }
                        }

                        // Recreate response with same body
                        const MediaType = Java.use("okhttp3.MediaType");
                        const ResponseBody = Java.use("okhttp3.ResponseBody");
                        const newBody = ResponseBody.create(body.contentType(), bytes);

                        const builder = response.newBuilder();
                        builder.body(newBody);
                        return builder.build();

                    } catch (e) {
                        // Return original on error
                        return response;
                    }
                }

                return response;
            };
        },
        onComplete: function () { }
    });

    console.log("[+] Hooked: okhttp3.RealCall.execute");

} catch (e) {
    console.log("[!] Call hook failed: " + e);
}

console.log("\n[✅] Enhanced interceptor READY");
console.log("[*] Storage: " + STORAGE_PATH);
console.log("[*] Waiting for episodes...\n");

// Stats reporter
setInterval(function () {
    if (stats.currentEpisode) {
        const mb = (stats.totalBytes / 1024 / 1024).toFixed(2);
        console.log("\n[📊] STATS:");
        console.log("    Episodes captured: " + stats.totalEpisodes);
        console.log("    Total segments: " + stats.totalSegments);
        console.log("    Total data: " + mb + " MB");
        console.log("    Current episode: " + stats.currentEpisode + " (" + currentEpisode.segmentCount + " segments)");
    }
}, 60000); // Every 60 seconds
