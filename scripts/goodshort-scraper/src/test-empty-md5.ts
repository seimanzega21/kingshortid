/**
 * Test with EMPTY appSignatureMD5 since Frida shows it's empty
 */

import { generateSign } from './sign-generator';

const params = {
    timestamp: '1769855063192',
    path: '/home/index',
    gaid: '3a527bd0-4a98-47e7-ac47-f592c165d870',
    androidId: 'ffffffffcf4ce71dcf4ce71d00000000',
    userToken: 'Bearer ZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SnlaV2RwYzNSbGNsUjVjR1VpT2lKUVJWSk5RVTVGVGxRaUxDSjFjMlZ5U1dRaU9qRTJNREExT0RReE4zMC5XYzA4LXpEOUxuaHBCREJkRENrMDBPQWxiLUtCa3ZKek9jbmg2Ump6MENF',
    appSignatureMD5: '' // Empty based on Frida extraction!
};

const expected = 'VTHYJWUtBYS5e0k4w/UuC3/uQnIHzRPrm7dMhdEWBnt5Uxm9DV4qxG/92PNTr6bfFTY8MiqjBmcV6gf6Bjm4xnCHEun1PU7bfROwwbGh08TiL3CjIefWBp27Uhit/gquZXk+pTn9XgyKVHtFYHGJBRgUg7Ps/etgAzVcmUdnXNP5uAg6demZORtW3Qv9iHv5Uctas4s0eV1idPafxnHGI7/FcdKItQf6ziWu4/WRQi+aM/+JF9sUO7yqD0KLTM76TIEkq8QTyGbksYHtXFA9enM3jWbaMjhts5jpI4Jb3yQQPpewMDbnbLqcKhGfvXIk4tppoYi4wx/21BIpBFW5cQ==';

console.log('Testing with EMPTY appSignatureMD5...');
console.log('');

const sign = generateSign(params);

console.log('Generated sign:');
console.log(sign);
console.log('');
console.log('Expected sign:');
console.log(expected);
console.log('');
console.log('Match:', sign === expected ? '✅ YES!' : '❌ NO');

// If still not match, calculate input length
const input = params.path + params.timestamp + params.gaid + params.androidId +
    params.userToken + params.appSignatureMD5 + 'com.newreading.goodreels';
console.log('');
console.log('Our input length:', input.length);
console.log('Expected from app: 315');
