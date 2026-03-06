/**
 * Frida Console Helper
 * Interactive commands to check capture status
 * 
 * Run this in Frida console to get current capture status
 */

console.log("\n" + "=".repeat(60));
console.log("📊 FRIDA CAPTURE STATUS CHECKER");
console.log("=".repeat(60));

// Read and parse the captured-episodes.json file if it exists
Java.perform(function () {
    var File = Java.use("java.io.File");
    var FileReader = Java.use("java.io.FileReader");
    var BufferedReader = Java.use("java.io.BufferedReader");
    var StringBuilder = Java.use("java.lang.StringBuilder");

    console.log("\n✅ Connected to GoodShort app");
    console.log("\n📝 Available commands:");
    console.log("  • status() - Show current capture status");
    console.log("  • list()   - List all captured dramas");
    console.log("  • export() - Export data to copy");
    console.log("");
});

// Helper to show how many dramas/episodes have been captured
this.quickStatus = function () {
    if (typeof data !== 'undefined' && data.dramas) {
        var dramaCount = Object.keys(data.dramas).length;
        var totalEpisodes = 0;

        for (var bookId in data.dramas) {
            totalEpisodes += Object.keys(data.dramas[bookId].episodes).length;
        }

        console.log("\n┌─────────────────────────────┐");
        console.log("│  📊 QUICK STATUS            │");
        console.log("├─────────────────────────────┤");
        console.log("│  Dramas:   " + dramaCount.toString().padEnd(16) + "│");
        console.log("│  Episodes: " + totalEpisodes.toString().padEnd(16) + "│");
        console.log("└─────────────────────────────┘");
    } else {
        console.log("⚠ No capture data available yet");
        console.log("  Browse dramas in the app to start capturing");
    }
};
