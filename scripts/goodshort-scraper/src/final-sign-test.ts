/**
 * FINAL COMPREHENSIVE TEST
 * Using ALL extracted parameters from Frida
 */

import { generateSign } from './sign-generator';
import crypto from 'crypto';

// EXACT parameters from Frida capture
const EXACT_PARAMS = {
    path: '/home/index',
    timestamp: '1769855063192',
    gaid: '3a527bd0-4a98-47e7-ac47-f592c165d870',
    androidId: 'ffffffffcf4ce71dcf4ce71d00000000',
    // Full userToken (199 chars)
    userToken: 'Bearer ZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SnlaV2RwYzNSbGNsUjVjR1VpT2lKUVJWSk5RVTVGVGxRaUxDSjFjMlZ5U1dRaU9qRTJNREExT0RReE4zMC5XYzA4LXpEOUxuaHBCREJkRENrMDBPQWxiLUtCa3ZKek9jbmg2Ump6MENF',
    appSignatureMD5: '', // Empty based on Frida extraction
    pkna: 'com.newreading.goodreels'
};

// Expected captured sign from headers
const CAPTURED_SIGN = 'VTHYJWUtBYS5e0k4w/UuC3/uQnIHzRPrm7dMhdEWBnt5Uxm9DV4qxG/92PNTr6bfFTY8MiqjBmcV6gf6Bjm4xnCHEun1PU7bfROwwbGh08TiL3CjIefWBp27Uhit/gquZXk+pTn9XgyKVHtFYHGJBRgUg7Ps/etgAzVcmUdnXNP5uAg6demZORtW3Qv9iHv5Uctas4s0eV1idPafxnHGI7/FcdKItQf6ziWu4/WRQi+aM/+JF9sUO7yqD0KLTM76TIEkq8QTyGbksYHtXFA9enM3jWbaMjhts5jpI4Jb3yQQPpewMDbnbLqcKhGfvXIk4tppoYi4wx/21BIpBFW5cQ==';

console.log('================================================');
console.log('FINAL COMPREHENSIVE SIGN GENERATION TEST');
console.log('================================================\n');

console.log('Parameters:');
console.log('  path:', EXACT_PARAMS.path);
console.log('  timestamp:', EXACT_PARAMS.timestamp);
console.log('  gaid:', EXACT_PARAMS.gaid);
console.log('  androidId:', EXACT_PARAMS.androidId);
console.log('  userToken length:', EXACT_PARAMS.userToken.length);
console.log('  appSignatureMD5:', EXACT_PARAMS.appSignatureMD5 || '(empty)');
console.log('  pkna:', EXACT_PARAMS.pkna);
console.log('');

// Build input string as per our implementation
const ourInput = EXACT_PARAMS.path + EXACT_PARAMS.timestamp + EXACT_PARAMS.gaid +
    EXACT_PARAMS.androidId + EXACT_PARAMS.userToken +
    EXACT_PARAMS.appSignatureMD5 + EXACT_PARAMS.pkna;

console.log('Our input string:');
console.log('  Length:', ourInput.length);
console.log('  Expected:', 315);
console.log('  Match:', ourInput.length === 315 ? '✅' : '❌');
console.log('');

// Generate our sign
const ourSign = generateSign({
    timestamp: EXACT_PARAMS.timestamp,
    path: EXACT_PARAMS.path,
    gaid: EXACT_PARAMS.gaid,
    androidId: EXACT_PARAMS.androidId,
    userToken: EXACT_PARAMS.userToken,
    appSignatureMD5: EXACT_PARAMS.appSignatureMD5
});

console.log('Our generated sign (first 80):');
console.log(' ', ourSign.substring(0, 80));
console.log('');

console.log('Captured sign (first 80):');
console.log(' ', CAPTURED_SIGN.substring(0, 80));
console.log('');

console.log('MATCH:', ourSign === CAPTURED_SIGN ? '✅ SUCCESS!' : '❌ DIFFERENT');

if (ourSign !== CAPTURED_SIGN) {
    console.log('\n');
    console.log('Debug info:');
    console.log('  Our sign length:', ourSign.length);
    console.log('  Captured sign length:', CAPTURED_SIGN.length);
    console.log('');

    // Check if maybe they're the same bytes but different encoding
    const ourBytes = Buffer.from(ourSign, 'base64');
    const capturedBytes = Buffer.from(CAPTURED_SIGN, 'base64');
    console.log('  Our sign decoded bytes:', ourBytes.length);
    console.log('  Captured sign decoded bytes:', capturedBytes.length);
}

console.log('');
console.log('================================================');
