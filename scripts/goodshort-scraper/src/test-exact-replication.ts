/**
 * Replicate EXACT captured request
 * Use exact same timestamp and parameters from capture
 */

import { generateSign } from './sign-generator';
import axios from 'axios';

// EXACT values from captured-headers.json
const EXACT_TIMESTAMP = "1769855063192";
const EXACT_PATH = "/home/index";
const EXACT_GAID = "3a527bd0-4a98-47e7-ac47-f592c165d870";
const EXACT_ANDROID_ID = "ffffffffcf4ce71dcf4ce71d00000000";
const EXACT_USER_TOKEN = ""; // Try empty first
const EXACT_APK_MD5 = "CA28D371148D19831C9995293CD1CACE";

const EXACT_CAPTURED_SIGN = "VTHYJWUtBYS5e0k4w/UuC3/uQnIHzRPrm7dMhdEWBnt5Uxm9DV4qxG/92PNTr6bfFTY8MiqjBmcV6gf6Bjm4xnCHEun1PU7bfROwwbGh08TiL3CjIefWBp27Uhit/gquZXk+pTn9XgyKVHtFYHGJBRgUg7Ps/etgAzVcmUdnXNP5uAg6demZORtW3Qv9iHv5Uctas4s0eV1idPafxnHGI7/FcdKItQf6ziWu4/WRQi+aM/+JF9sUO7yqD0KLTM76TIEkq8QTyGbksYHtXFA9enM3jWbaMjhts5jpI4Jb3yQQPpewMDbnbLqcKhGfvXIk4tppoYi4wx/21BIpBFW5cQ==";

console.log('========================================');
console.log('Replicating EXACT Captured Request');
console.log('========================================\n');

console.log('Input params:');
console.log('  timestamp:', EXACT_TIMESTAMP);
console.log('  path:', EXACT_PATH);
console.log('  gaid:', EXACT_GAID);
console.log('  androidId:', EXACT_ANDROID_ID);
console.log('  userToken:', EXACT_USER_TOKEN || '(empty)');
console.log('  appSignatureMD5:', EXACT_APK_MD5);
console.log('');

// Build input string
const inputString =
    EXACT_PATH +
    EXACT_TIMESTAMP +
    EXACT_GAID +
    EXACT_ANDROID_ID +
    EXACT_USER_TOKEN +
    EXACT_APK_MD5 +
    'com.newreading.goodreels';

console.log('Input string for signing:');
console.log(inputString);
console.log('\nLength:', inputString.length);
console.log('');

// Generate our sign
const ourSign = generateSign({
    timestamp: EXACT_TIMESTAMP,
    path: EXACT_PATH,
    gaid: EXACT_GAID,
    androidId: EXACT_ANDROID_ID,
    userToken: EXACT_USER_TOKEN,
    appSignatureMD5: EXACT_APK_MD5
});

console.log('Our generated sign:');
console.log(ourSign);
console.log('');

console.log('Captured sign from app:');
console.log(EXACT_CAPTURED_SIGN);
console.log('');

console.log('Signs match:', ourSign === EXACT_CAPTURED_SIGN ? '✅ YES!' : '❌ NO');
console.log('');

if (ourSign !== EXACT_CAPTURED_SIGN) {
    console.log('========================================');
    console.log('MISMATCH DETECTED!');
    console.log('========================================');
    console.log('This means our input string or signing process is different.');
    console.log('');
    console.log('Possible issues:');
    console.log('1. Wrong APK signature MD5');
    console.log('2. Missing parameter in input');
    console.log('3. Different parameter order');
    console.log('4. Wrong private key');
    console.log('5. userToken is not empty');
    console.log('========================================\n');
}
