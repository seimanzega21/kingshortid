/**
 * CORRECTED Sign Generator based on deep debugging
 * 
 * DISCOVERY: The sign input format is:
 * timestamp={timestamp}{JSON_BODY_STRINGIFIED}{gaid}{androidId}{userToken}{APK_MD5}{packageName}
 */

import crypto from 'crypto';

// CORRECTED APK Signature MD5 from deep debugging!
const CORRECT_APK_MD5 = '919326DD9A742D064502468E1BF11144';

const PACKAGE_NAME = 'com.newreading.goodreels';

// RSA Private Key from original sign-generator.ts
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
    "PiT6gPFlvjEtLwVFTNSMOsXmJqzXnMdC5FaGEiP/zKeep9dFVdZ1PcFRLjb9ZTMJ" +
    "x9piOdxxkAmZ93RaC4cRZlWvkrWrNiGqYSPmyoX5GwKBgFTI7IXpncLsrEebkNJw" +
    "x8XD0qgE9IbWg0LRUNn8lGHzGDT2mi/n1P/0tDBWVT3bfBvPGDvDLqiymmbKOwJm" +
    "a5xWvqR1VZqF6btDgJ4AOHcnOvhGOL7IN9IkeRp2K+e2EIXI+XeoOjGqNw+TXrYS" +
    "2jBKONRLxGbqGbvFKmJHGYsK";

function getPrivateKey(): string {
    const der = Buffer.from(RSA_PRIVATE_KEY_BASE64, 'base64');
    const pem = `-----BEGIN PRIVATE KEY-----\n${RSA_PRIVATE_KEY_BASE64.match(/.{1,64}/g)?.join('\n')}\n-----END PRIVATE KEY-----`;
    return pem;
}


export interface SignParamsV2 {
    timestamp: string;
    body: object;  // Request body - THIS IS INCLUDED IN SIGN!
    gaid?: string;
    androidId?: string;
    userToken?: string;
}

/**
 * Generate sign using CORRECT format discovered from deep debugging
 */
export function generateSignV2(params: SignParamsV2): string {
    const {
        timestamp,
        body,
        gaid = '',
        androidId = '',
        userToken = ''
    } = params;

    // Build input string in CORRECT order
    // Format: timestamp={timestamp}{JSON_BODY}{gaid}{androidId}{userToken}{MD5}{packageName}
    const bodyJson = JSON.stringify(body);
    const input = `timestamp=${timestamp}${bodyJson}${gaid}${androidId}${userToken}${CORRECT_APK_MD5}${PACKAGE_NAME}`;

    console.log('\n=== Sign Generation (V2 CORRECTED) ===');
    console.log('Timestamp:', timestamp);
    console.log('Body JSON:', bodyJson.substring(0, 50) + '...');
    console.log('GAID:', gaid);
    console.log('AndroidID:', androidId);
    console.log('UserToken (len):', userToken.length);
    console.log('APK MD5:', CORRECT_APK_MD5);
    console.log('Package:', PACKAGE_NAME);
    console.log('Input length:', input.length);
    console.log('Input preview:', input.substring(0, 100) + '...');

    try {
        const privateKey = getPrivateKey();
        const sign = crypto.createSign('RSA-SHA256');
        sign.update(input, 'utf8');
        sign.end();

        const signature = sign.sign(privateKey, 'base64');
        console.log('Generated sign (first 60):', signature.substring(0, 60));

        return signature;
    } catch (error) {
        console.error('Sign generation failed:', error);
        throw error;
    }
}

// Test with sample data
if (require.main === module) {
    console.log('Testing corrected sign generator...\n');

    const testSign = generateSignV2({
        timestamp: '1769885080122',
        body: {
            addRecently: true,
            chapterIndex: 1,
            bookId: '31000960344'
        },
        gaid: '3a527bd0-4a98-47e7-ac47-f592c165d870',
        androidId: 'ffffffffcf4ce71dcf4ce71d00000000',
        userToken: 'Bearer ZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SnlaV2RwYzNSbGNsUjVjR1VpT2lKUVJWSk5RVTVGVGxRaUxDSjFjMlZ5U1dRaU9qRTJNREExT0RReE4zMC5XYzA4LXpEOUxuaHBCREJkRENrMDBPQWxiLUtCa3ZKek9jbmg2Ump6MENF'
    });

    console.log('\n=== Full Sign ===');
    console.log(testSign);
}
