/**
 * Test different APK signature MD5 variations
 */

import { generateSign } from './sign-generator';

const BASE_PARAMS = {
    timestamp: "1769855063192",
    path: "/home/index",
    gaid: "3a527bd0-4a98-47e7-ac47-f592c165d870",
    androidId: "ffffffffcf4ce71dcf4ce71d00000000",
    userToken: ""
};

const CAPTURED_SIGN = "VTHYJWUtBYS5e0k4w/UuC3/uQnIHzRPrm7dMhdEWBnt5Uxm9DV4qxG/92PNTr6bfFTY8MiqjBmcV6gf6Bjm4xnCHEun1PU7bfROwwbGh08TiL3CjIefWBp27Uhit/gquZXk+pTn9XgyKVHtFYHGJBRgUg7Ps/etgAzVcmUdnXNP5uAg6demZORtW3Qv9iHv5Uctas4s0eV1idPafxnHGI7/FcdKItQf6ziWu4/WRQi+aM/+JF9sUO7yqD0KLTM76TIEkq8QTyGbksYHtXFA9enM3jWbaMjhts5jpI4Jb3yQQPpewMDbnbLqcKhGfvXIk4tppoYi4wx/21BIpBFW5cQ==";

console.log('Testing APK Signature MD5 Variations...\n');

const md5Variations = [
    { name: 'Uppercase (our extracted)', value: 'CA28D371148D19831C9995293CD1CACE' },
    { name: 'Lowercase', value: 'ca28d371148d19831c9995293cd1cace' },
    { name: 'Empty', value: '' },
    { name: 'Just "CA28D371"', value: 'CA28D371' },
    { name: 'Different format', value: 'CA:28:D3:71:14:8D:19:83:1C:99:95:29:3CD1CACE' }
];

let found = false;

md5Variations.forEach((variation, i) => {
    console.log(`Test ${i + 1}: ${variation.name}`);
    console.log(`  MD5: "${variation.value}"`);

    const sign = generateSign({
        ...BASE_PARAMS,
        appSignatureMD5: variation.value
    });

    const matches = sign === CAPTURED_SIGN;
    console.log(`  Match: ${matches ? '✅ YES! FOUND IT!' : '❌ No'}`);
    console.log(`  Sign: ${sign.substring(0, 60)}...`);
    console.log('');

    if (matches) {
        found = true;
        console.log('🎉 SOLUTION FOUND!');
        console.log(`Use APK Signature MD5: "${variation.value}"\n`);
    }
});

if (!found) {
    console.log('========================================');
    console.log('None of the MD5 variations matched!');
    console.log('========================================');
    console.log('This means the issue is NOT the APK MD5 format.');
    console.log('Must be:');
    console.log('  - userToken is not empty (need to extract from app)');
    console.log('  - OR different input parameter entirely');
    console.log('  - OR wrong private key');
    console.log('========================================\n');
}
