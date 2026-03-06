/**
 * GoodShort SSL Unpinning Script for Frida
 * Use with mitmproxy to capture all traffic
 * 
 * Usage:
 *   frida -U -f com.newreading.goodreels -l frida/ssl_unpin_for_mitm.js --no-pause
 * 
 * Then configure Android proxy to point to mitmproxy
 */

console.log("\n" + "=".repeat(60));
console.log("🔓 GoodShort SSL Unpinning for mitmproxy");
console.log("=".repeat(60) + "\n");

Java.perform(function () {
    console.log("[*] Bypassing SSL Pinning...\n");

    // === Method 1: OkHttp CertificatePinner ===
    try {
        var CertificatePinner = Java.use('okhttp3.CertificatePinner');
        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function (hostname, peerCertificates) {
            console.log('[+] OkHttp CertificatePinner.check() bypassed for: ' + hostname);
            return;
        };

        CertificatePinner.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = function (hostname, peerCertificates) {
            console.log('[+] OkHttp CertificatePinner.check() bypassed for: ' + hostname);
            return;
        };
        console.log('[✓] OkHttp CertificatePinner hooked');
    } catch (e) {
        console.log('[-] OkHttp CertificatePinner not found: ' + e);
    }

    // === Method 2: OkHttp3 Builder ===
    try {
        var OkHttpClient = Java.use('okhttp3.OkHttpClient$Builder');
        OkHttpClient.certificatePinner.implementation = function (certificatePinner) {
            console.log('[+] OkHttp3 Builder.certificatePinner() bypassed');
            return this;
        };
        console.log('[✓] OkHttp3 Builder hooked');
    } catch (e) {
        console.log('[-] OkHttp3 Builder not found: ' + e);
    }

    // === Method 3: TrustManager ===
    try {
        var TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
        TrustManagerImpl.verifyChain.implementation = function (untrustedChain, trustAnchorChain, host, clientAuth, ocspData, tlsSctData) {
            console.log('[+] TrustManagerImpl.verifyChain() bypassed for: ' + host);
            return untrustedChain;
        };
        console.log('[✓] TrustManagerImpl hooked');
    } catch (e) {
        console.log('[-] TrustManagerImpl not found');
    }

    // === Method 4: X509TrustManager ===
    try {
        var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
        var SSLContext = Java.use('javax.net.ssl.SSLContext');

        var TrustManager = Java.registerClass({
            name: 'com.mitmbypass.TrustManager',
            implements: [X509TrustManager],
            methods: {
                checkClientTrusted: function (chain, authType) { },
                checkServerTrusted: function (chain, authType) { },
                getAcceptedIssuers: function () { return []; }
            }
        });

        var TrustManagers = [TrustManager.$new()];
        var sslContext = SSLContext.getInstance('TLS');
        sslContext.init(null, TrustManagers, null);

        console.log('[✓] Custom X509TrustManager installed');
    } catch (e) {
        console.log('[-] X509TrustManager bypass: ' + e);
    }

    // === Method 5: SSLSocket ===
    try {
        var SSLSocket = Java.use('com.android.org.conscrypt.OpenSSLSocketImpl');
        SSLSocket.verifyCertificateChain.implementation = function (certChain, authMethod) {
            console.log('[+] SSLSocket.verifyCertificateChain() bypassed');
        };
        console.log('[✓] SSLSocket hooked');
    } catch (e) {
        console.log('[-] SSLSocket not found');
    }

    // === Method 6: WebViewClient ===
    try {
        var WebViewClient = Java.use('android.webkit.WebViewClient');
        WebViewClient.onReceivedSslError.implementation = function (view, handler, error) {
            console.log('[+] WebViewClient SSL error ignored');
            handler.proceed();
        };
        console.log('[✓] WebViewClient hooked');
    } catch (e) {
        console.log('[-] WebViewClient not found');
    }

    // === Method 7: Network Security Config ===
    try {
        var NetworkSecurityConfig = Java.use('android.security.net.config.NetworkSecurityConfig');
        NetworkSecurityConfig.isCleartextTrafficPermitted.overload().implementation = function () {
            console.log('[+] Cleartext traffic permitted');
            return true;
        };
        console.log('[✓] NetworkSecurityConfig hooked');
    } catch (e) {
        console.log('[-] NetworkSecurityConfig not found');
    }

    // === Method 8: HostnameVerifier ===
    try {
        var HostnameVerifier = Java.use('javax.net.ssl.HostnameVerifier');
        var HttpsURLConnection = Java.use('javax.net.ssl.HttpsURLConnection');

        HttpsURLConnection.setDefaultHostnameVerifier.implementation = function (hostnameVerifier) {
            console.log('[+] Default HostnameVerifier bypassed');
            return;
        };
        console.log('[✓] HostnameVerifier hooked');
    } catch (e) {
        console.log('[-] HostnameVerifier not found');
    }

    console.log("\n" + "=".repeat(60));
    console.log("✅ SSL Unpinning Complete!");
    console.log("=".repeat(60));
    console.log("\n📱 Now configure Android proxy:");
    console.log("   adb shell settings put global http_proxy 10.0.2.2:8888");
    console.log("\n🌐 Then run mitmproxy:");
    console.log("   mitmdump -s goodshort_mitmproxy.py -p 8888");
    console.log("\n📲 Browse GoodShort app - traffic will be captured!\n");
});
