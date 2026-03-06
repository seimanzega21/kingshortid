/**
 * GoodShort Auto Token Extractor
 * 
 * Automatically extracts and refreshes authentication tokens
 * Saves to config file for use by other scripts
 * 
 * Usage:
 *   frida -U -f com.newreading.goodreels -l frida/auto-token-extractor.js
 */

console.log("\n" + "=".repeat(70));
console.log("🔐 GoodShort Auto Token Extractor");
console.log("=".repeat(70) + "\n");

const fs = Java.use("java.io.File");
const FileWriter = Java.use("java.io.FileWriter");

// Token storage
var tokens = {
    userToken: null,
    gaid: null,
    androidId: null,
    deviceInfo: {},
    lastUpdate: null,
    autoRefresh: true
};

// Config file path (app's external storage)
var CONFIG_PATH = "/sdcard/goodshort_tokens.json";

function saveTokens() {
    try {
        var json = JSON.stringify(tokens, null, 2);
        var file = fs.$new(CONFIG_PATH);
        var writer = FileWriter.$new(file);
        writer.write(json);
        writer.close();

        console.log("\n✅ Tokens saved to: " + CONFIG_PATH);
        console.log("📋 Copy to your PC:");
        console.log("   adb pull " + CONFIG_PATH + " .\n");

        return true;
    } catch (e) {
        console.error("❌ Failed to save tokens: " + e);
        return false;
    }
}

function extractDeviceInfo() {
    try {
        // Get Settings.Secure for Android ID
        var Settings = Java.use("android.provider.Settings$Secure");
        var context = Java.use("android.app.ActivityThread").currentApplication().getApplicationContext();

        tokens.androidId = Settings.getString(context.getContentResolver(), "android_id");

        console.log("📱 Android ID: " + tokens.androidId);
    } catch (e) {
        console.error("⚠️  Could not get Android ID: " + e);
    }

    try {
        // Try to get GAID from SharedPreferences
        var context = Java.use("android.app.ActivityThread").currentApplication().getApplicationContext();
        var prefs = context.getSharedPreferences("sp_data", 0);

        var allPrefs = prefs.getAll();
        var keys = allPrefs.keySet().toArray();

        for (var i = 0; i < keys.length; i++) {
            var key = keys[i].toString();
            var value = allPrefs.get(keys[i]);

            if (key.toLowerCase().indexOf("gaid") !== -1 ||
                key.toLowerCase().indexOf("google") !== -1 ||
                key.toLowerCase().indexOf("ad") !== -1) {
                console.log("  📊 " + key + ": " + value);

                if (value && value.toString().length > 20) {
                    tokens.gaid = value.toString();
                }
            }
        }

        if (tokens.gaid) {
            console.log("📊 GAID: " + tokens.gaid);
        }
    } catch (e) {
        console.error("⚠️  Could not extract GAID: " + e);
    }
}

Java.perform(function () {
    console.log("[*] Hooking authentication systems...\n");

    // Extract device info first
    extractDeviceInfo();

    // Hook 1: SharedPreferences for user token
    try {
        var SharedPreferences = Java.use("android.content.SharedPreferences");
        var Editor = Java.use("android.content.SharedPreferences$Editor");

        Editor.putString.overload('java.lang.String', 'java.lang.String').implementation = function (key, value) {
            if (key && value) {
                var keyStr = key.toString();
                var valueStr = value.toString();

                // Check if it's a token (long string, starts with specific patterns)
                if (valueStr.length > 50 &&
                    (keyStr.toLowerCase().indexOf("token") !== -1 ||
                        keyStr.toLowerCase().indexOf("auth") !== -1 ||
                        keyStr.toLowerCase().indexOf("user") !== -1 ||
                        valueStr.startsWith("Bearer ") ||
                        valueStr.startsWith("eyJ"))) { // JWT pattern

                    console.log("\n🔑 [TOKEN DETECTED]");
                    console.log("   Key: " + keyStr);
                    console.log("   Value: " + valueStr.substring(0, 50) + "...");

                    tokens.userToken = valueStr;
                    tokens.lastUpdate = new Date().toISOString();

                    if (tokens.autoRefresh) {
                        saveTokens();
                    }
                }
            }

            return this.putString(key, value);
        };
    } catch (e) {
        console.error("⚠️  Failed to hook SharedPreferences: " + e);
    }

    // Hook 2: OkHttp headers to catch Authorization
    try {
        var Request = Java.use("okhttp3.Request");
        var RequestBuilder = Java.use("okhttp3.Request$Builder");

        RequestBuilder.addHeader.overload('java.lang.String', 'java.lang.String').implementation = function (name, value) {
            if (name.toString().toLowerCase() === "authorization") {
                console.log("\n🔑 [AUTH HEADER]");
                console.log("   " + name + ": " + value.substring(0, 50) + "...");

                tokens.userToken = value.toString();
                tokens.lastUpdate = new Date().toISOString();

                if (tokens.autoRefresh) {
                    saveTokens();
                }
            }

            return this.addHeader(name, value);
        };
    } catch (e) {
        console.error("⚠️  Failed to hook OkHttp: " + e);
    }

    // Hook 3: Sign generator to get all params
    try {
        // Look for sign generation methods
        Java.enumerateLoadedClasses({
            onMatch: function (className) {
                if (className.indexOf("AppUtils") !== -1 ||
                    className.indexOf("SignUtil") !== -1 ||
                    className.indexOf("Signature") !== -1) {

                    try {
                        var cls = Java.use(className);
                        var methods = cls.class.getDeclaredMethods();

                        for (var i = 0; i < methods.length; i++) {
                            var methodName = methods[i].getName();

                            if (methodName.toLowerCase().indexOf("sign") !== -1 ||
                                methodName.toLowerCase().indexOf("token") !== -1) {
                                console.log("  📍 Found: " + className + "." + methodName);
                            }
                        }
                    } catch (e) {
                        // Skip
                    }
                }
            },
            onComplete: function () { }
        });
    } catch (e) {
        console.error("⚠️  Failed to enumerate classes: " + e);
    }

    console.log("\n[✓] Hooks installed!\n");
    console.log("📱 Now use the app normally");
    console.log("🔄 Tokens will auto-save when detected");
    console.log("\n📋 Commands:");
    console.log("   status()  - Show current tokens");
    console.log("   save()    - Force save to file");
    console.log("   export()  - Print JSON to console");
    console.log("");
});

// RPC Exports
rpc.exports = {
    status: function () {
        console.log("\n" + "=".repeat(70));
        console.log("TOKEN STATUS");
        console.log("=".repeat(70));

        console.log("\n🔑 User Token:");
        if (tokens.userToken) {
            console.log("   " + tokens.userToken.substring(0, 60) + "...");
            console.log("   Length: " + tokens.userToken.length + " chars");
        } else {
            console.log("   ❌ Not captured yet");
        }

        console.log("\n📱 Device Info:");
        console.log("   Android ID: " + (tokens.androidId || "❌ Not found"));
        console.log("   GAID: " + (tokens.gaid || "❌ Not found"));

        console.log("\n⏰ Last Update:");
        console.log("   " + (tokens.lastUpdate || "Never"));

        console.log("\n" + "=".repeat(70) + "\n");

        return tokens;
    },

    save: function () {
        console.log("\n💾 Forcing save...");
        if (saveTokens()) {
            return "✅ Saved successfully to " + CONFIG_PATH;
        } else {
            return "❌ Failed to save";
        }
    },

    export: function () {
        console.log("\n" + "=".repeat(70));
        console.log("EXPORTED TOKEN DATA");
        console.log("=".repeat(70));
        console.log(JSON.stringify(tokens, null, 2));
        console.log("=".repeat(70) + "\n");

        return tokens;
    },

    setAutoRefresh: function (enabled) {
        tokens.autoRefresh = enabled;
        console.log("🔄 Auto-refresh: " + (enabled ? "ENABLED" : "DISABLED"));
        return enabled;
    }
};

// Global shortcuts
globalThis.status = function () { return rpc.exports.status(); };
globalThis.save = function () { return rpc.exports.save(); };
globalThis.export = function () { return rpc.exports.export(); };
