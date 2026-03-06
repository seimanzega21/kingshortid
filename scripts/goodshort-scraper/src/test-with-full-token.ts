/**
 * Test sign generation with COMPLETE parameters including userToken
 */

import { generateSign } from './sign-generator';

// COMPLETE parameters from Frida extraction  
const COMPLETE_PARAMS = {
    timestamp: '1769855063192',
    path: '/home/index',
    gaid: '3a527bd0-4a98-47e7-ac47-f592c165d870',
    androidId: 'ffffffffcf4ce71dcf4ce71d00000000',
    // The MISSING PIECE - userToken is NOT empty!
    userToken: 'Bearer ZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SnlaV2RwYzNSbGNsUjVjR1VpT2lKUVJWSk5RVTVGVGxRaUxDSjFjMlZ5U1dRaU9qRTJNREExT0RReE4zMC5XYzA4LXpEOUxuaHBCREJkRENrMDBPQWxiLUtCa3ZKek9jbmg2Ump6MENF',
    appSignatureMD5: 'CA28D371148D19831C9995293CD1CACE'
};

// Expected sign from captured headers
const EXPECTED_SIGN = 'VTHYJWUtBYS5e0k4w/UuC3/uQnIHzRPrm7dMhdEWBnt5Uxm9DV4qxG/92PNTr6bfFTY8MiqjBmcV6gf6Bjm4xnCHEun1PU7bfROwwbGh08TiL3CjIefWBp27Uhit/gquZXk+pTn9XgyKVHtFYHGJBRgUg7Ps/etgAzVcmUdnXNP5uAg6demZORtW3Qv9iHv5Uctas4s0eV1idPafxnHGI7/FcdKItQf6ziWu4/WRQi+aM/+JF9sUO7yqD0KLTM76TIEkq8QTyGbksYHtXFA9enM3jWbaMjhts5jpI4Jb3yQQPpewMDbnbLqcKhGfvXIk4tppoYi4wx/21BIpBFW5cQ==';

console.log('========================================');
console.log('Testing with COMPLETE Parameters');
console.log('========================================\n');

console.log('Parameters:');
console.log(JSON.stringify(COMPLETE_PARAMS, null, 2));
console.log('\n');

// Try with full userToken
console.log('Test 1: With full Bearer token as userToken...');
const sign1 = generateSign(COMPLETE_PARAMS);
console.log('Generated:', sign1.substring(0, 60) + '...');
console.log('Expected:', EXPECTED_SIGN.substring(0, 60) + '...');
console.log('Match:', sign1 === EXPECTED_SIGN ? '✅ YES!' : '❌ NO');
console.log('');

// Try without "Bearer " prefix
console.log('Test 2: Without "Bearer " prefix...');
const sign2 = generateSign({
    ...COMPLETE_PARAMS,
    userToken: COMPLETE_PARAMS.userToken.replace('Bearer ', '')
});
console.log('Generated:', sign2.substring(0, 60) + '...');
console.log('Match:', sign2 === EXPECTED_SIGN ? '✅ YES!' : '❌ NO');
console.log('');

// Try with just the JWT payload (decoded)
console.log('Test 3: With empty userToken (for comparison)...');
const sign3 = generateSign({
    ...COMPLETE_PARAMS,
    userToken: ''
});
console.log('Generated:', sign3.substring(0, 60) + '...');
console.log('Match:', sign3 === EXPECTED_SIGN ? '✅ YES!' : '❌ NO');

console.log('\n========================================');
