/**
 * GoodShort Sign Generation Algorithm
 * Reverse engineered from com.newreading.goodreels APK
 */

import * as crypto from 'crypto';

// RSA Private Key extracted from APK (class `a`)
const RSA_PRIVATE_KEY_BASE64 =
    "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDLwHQE9g2+/DJm" +
    "iVtNS6v0SmHKAEzGaClFMHMNszfi5GDkrA9SjT1Z87tScD2feSSuuKJIoSYL1o3m" +
    "qgmX2pCN/5rPzOifJ6gQjGZjLuvuxmvSRk8jHqsPoqj/QH6qhF5n2Mpr5oirGD9I" +
    "Ug3RRtdy0RfRuXxHLCnYhKfXKP+TdcK/1Hi/vPONlCpJo7ph62KVeUD+qACYZUNj" +
    "diZxklZZASac24OjBdFZOd/ZtINM4wOaHFpwHmnoq89qM1MP09gJc7tPlPONFoWI" +
    "AVpfwjtjRsCbFuGQdBf7FlEsxivef2nHFN8J9Q+aqE1wr+ouNbbUkEebYqbt2ROT" +
    "Pe7xCJnfAgMBAAECggEBAK3nFR8m45SerGXX1pWigKGA2vYOS3kMbi0frROEY67E" +
    "Pe7u7CUJZ9Pes4MpSW9TdnuqGtjishZoibTWbFmvsrF/+CJkQieVMVzueHUvFzA1" +
    "KtHOML1I77fonVU/Nt1THUCFSD/QA9YEW/7eCe0VCc51qF7YcbpNd2nVz2tVEs5H" +
    "rb1Q0WSdxXaIIyFH4vNS9Xgx4ZY2ULzaJePCbEZcUwFLiJQtIWslGcCDALFyPMN6" +
    "W9PKMFo96l0+KruleKfuiTCNzG94Vxe3ClAO64VIa65cSXu6DSUxiD1kedxDPRNE" +
    "sZU9qfwNi2gFJCa97KUMBcL2M4VV8guIh4QXQwGoTAECgYEA896OhcFRQXryCAHR" +
    "1+pLx3+aqM7qKf9qJWGh+lw/FWBB7cYQ3p+e9BomoQS5OdQcLGy2cTc38zMVvESN" +
    "Ek+VS81VnCnVDTKC9vGPvuRItas5RKjNxAQEMJdudGlweEwQqkDlFRktuXwXIRfm" +
    "zoA2iV+OUkJW5CDw81+hqMMsRpsCgYEA1eMJiw98fdeya1FJ9PE5x9lZyjyFIQ3y" +
    "dsRtSetmeDIETX2AlkHC0HqySbjsIyXsxmq8AajfHraShf6eZeOBsP+sfOPS6J+j" +
    "N9reS7gpVbl7EYL3D6OVMBuwZYv9ILkWj6lpfrFBvK8v32eRXgJjJ9LBkAXROBpC" +
    "QPMHvPwpTA0CgYA989cPIbpLwTkFUbkGeg4AQ2l94vrX6nwDvRbSLGcWPhrhlcSp" +
    "WbGe35napAGOMFVr7741asq67MpjxqJz+WW7GRHbl0D5llBw/ZL/8qyKAlKNH7kO" +
    "R9rsoTu9NSAOX3yIU+4eewQDsAOMM6893JJ+OZlFSncag0fS/ANshRCVawKBgQCf" +
    "rNUNCcyorgS29YK+5+948RyFTFUe7iia3d2xF5nyFXT83LrIceOcfFzpiLJRMxjm" +
    "r/wXSRj49tfATOu3qPbDSrxcqEBmBfd11WGrKZtCMixcUGddN4RC3Aj+ZlncuhDL" +
    "w2/Mc0xeLnMQ12LAygt4SXDTsmQU/BWGI2kdfyrdaQKBgDdzsoRSOh+tBtSRqEyc" +
    "4BgtfK/FyU7VQy3fUlaaBJEUY6FxE8Icn34VVEeN6YOEmAewEcyMcQQX2ZwQ2wIT" +
    "v4NssL8uDJ0y4K/TlL+2bomXri/nobvyaDsMfrX6grlQXe4YzVpzGUFbcW+QValH" +
    "pacnAjGejZkLM7KD2XaK1Ppf";

const PACKAGE_NAME = "com.newreading.goodreels";

// Convert Base64 private key to PEM format
function getPrivateKey(): string {
    return `-----BEGIN PRIVATE KEY-----\n${RSA_PRIVATE_KEY_BASE64}\n-----END PRIVATE KEY-----`;
}

export interface SignParams {
    timestamp: string;
    path: string;
    gaid?: string;           // Google Advertising ID
    androidId?: string;      // Android Device ID  
    userToken?: string;      // User authentication token
    appSignatureMD5?: string; // MD5 of APK signing certificate
}

/**
 * Generate sign header for GoodShort API
 * 
 * Algorithm (from NRKeyManager.getKey):
 * INPUT = path + timestamp + gaid + androidId + userToken + appSignatureMD5 + packageName
 * SIGN = Base64(RSA-SHA256-Sign(INPUT, privateKey))
 */
export function generateSign(params: SignParams): string {
    const {
        timestamp,
        path,
        gaid = '',
        androidId = '',
        userToken = '',
        appSignatureMD5 = ''
    } = params;

    // Build input string (from AppUtils.getSign and NRKeyManager.getKey)
    const input =
        path +              // API path
        timestamp +         // Timestamp
        gaid +              // Google Advertising ID
        androidId +         // Android Device ID
        userToken +         // User token
        appSignatureMD5 +   // APK signature MD5
        PACKAGE_NAME;       // Package name

    try {
        // Create RSA-SHA256 signature
        const privateKey = getPrivateKey();
        const sign = crypto.createSign('RSA-SHA256');
        sign.update(input, 'utf8');
        sign.end();

        // Sign and encode to Base64
        const signature = sign.sign(privateKey, 'base64');

        return signature;
    } catch (error) {
        console.error('Sign generation failed:', error);
        throw error;
    }
}

/**
 * Generate complete header data for API requests
 * (from AppUtils.getH5HeaderData)
 */
export function getH5HeaderData(params: SignParams): Record<string, string> {
    const sign = generateSign(params);

    return {
        'sign': sign,
        'timestamp': params.timestamp
    };
}

/**
 * Test function to verify sign generation
 */
export function testSignGeneration(): void {
    console.log('Testing sign generation...\n');

    const testParams: SignParams = {
        timestamp: Date.now().toString(),
        path: '/hwyclientreels/v1/drama/detail',
        gaid: 'test-gaid-12345',
        androidId: 'test-android-id-67890',
        userToken: 'test-token-abc',
        appSignatureMD5: 'A1B2C3D4E5F6'
    };

    console.log('Test Parameters:');
    console.log(JSON.stringify(testParams, null, 2));

    try {
        const headers = getH5HeaderData(testParams);
        console.log('\nGenerated Headers:');
        console.log(JSON.stringify(headers, null, 2));
        console.log('\n✅ Sign generation successful!');
    } catch (error) {
        console.error('\n❌ Sign generation failed:', error);
    }
}

// Run test if executed directly
if (require.main === module) {
    testSignGeneration();
}
