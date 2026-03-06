/**
 * Analyze captured real sign and headers
 */

// Captured from working API call
const CAPTURED_SIGN = "VTHYJWUtBYS5e0k4w/UuC3/uQnIHzRPrm7dMhdEWBnt5Uxm9DV4qxG/92PNTr6bfFTY8MiqjBmcV6gf6Bjm4xnCHEun1PU7bfROwwbGh08TiL3CjIefWBp27Uhit/gquZXk+pTn9XgyKVHtFYHGJBRgUg7Ps/etgAzVcmUdnXNP5uAg6demZORtW3Qv9iHv5Uctas4s0eV1idPafxnHGI7/FcdKItQf6ziWu4/WRQi+aM/+JF9sUO7yqD0KLTM76TIEkq8QTyGbksYHtXFA9enM3jWbaMjhts5jpI4Jb3yQQPpewMDbnbLqcKhGfvXIk4tppoYi4wx/21BIpBFW5cQ==";

const CAPTURED_URL = "https://api-akm.goodreels.com/hwycclientreels/home/index?timestamp=1769855063192";

const CAPTURED_AUTH_TOKEN = "Bearer ZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SnlaV2RwYzNSbGNsUjVjR1VpT2lKUVJWSk5RVTVGVGxRaUxDSjFjMlZ5U1dRaU9qRTJNREExT0RReE4zMC5XYzA4LXpEOUxuaHBCREJkRENrMDBPQWxiLUtCa3ZKek9jbmg2Ump6MENF";

console.log('========================================');
console.log('Analyzing Captured Real API Call');
console.log('========================================\n');

console.log('Captured Sign:');
console.log(CAPTURED_SIGN);
console.log('\nSign Length:', CAPTURED_SIGN.length);
console.log('');

// Decode Authorization token
const bearerToken = CAPTURED_AUTH_TOKEN.replace('Bearer ', '');
console.log('Bearer Token Base64:');
console.log(bearerToken);

try {
    const decoded = Buffer.from(bearerToken, 'base64').toString('utf-8');
    console.log('\nDecoded Bearer Token:');
    console.log(decoded);
    console.log('');
} catch (e) {
    console.log('\nFailed to decode bearer token');
}

// Extract timestamp from URL
const timestampMatch = CAPTURED_URL.match(/timestamp=(\d+)/);
const timestamp = timestampMatch ? timestampMatch[1] : '';

console.log('Captured Request Details:');
console.log('  Timestamp:', timestamp);
console.log('  Path:', '/hwycclientreels/home/index');
console.log('  GAID:', '3a527bd0-4a98-47e7-ac47-f592c165d870');
console.log('  Android ID:', 'ffffffffcf4ce71dcf4ce71d00000000');
console.log('  User ID:', '160058417');
console.log('');

console.log('========================================');
console.log('KEY INSIGHT:');
console.log('========================================');
console.log('The Authorization header contains a JWT token!');
console.log('This might be the "userToken" parameter needed for signing.');
console.log('');
console.log('Try using the FULL bearer token (base64) as userToken!');
console.log('========================================\n');
