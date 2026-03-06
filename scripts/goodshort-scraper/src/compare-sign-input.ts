/**
 * Compare our sign generation with captured real input
 */

import { generateSign } from './sign-generator';

// Our parameters
const OUR_PARAMS = {
    timestamp: '1769855063192', // Use same timestamp from captured headers
    path: '/home/index',
    gaid: '3a527bd0-4a98-47e7-ac47-f592c165d870',
    androidId: 'ffffffffcf4ce71dcf4ce71d00000000',
    userToken: '',
    appSignatureMD5: 'CA28D371148D19831C9995293CD1CACE'
};

console.log('========================================');
console.log('Sign Generation Comparison');
console.log('========================================\n');

console.log('Our Parameters:');
console.log(JSON.stringify(OUR_PARAMS, null, 2));
console.log('\n');

// Build input string exactly as our implementation does
const ourInput =
    OUR_PARAMS.path +
    OUR_PARAMS.timestamp +
    OUR_PARAMS.gaid +
    OUR_PARAMS.androidId +
    OUR_PARAMS.userToken +
    OUR_PARAMS.appSignatureMD5 +
    'com.newreading.goodreels';

console.log('Our Input String:');
console.log('Length:', ourInput.length);
console.log('First 100 chars:', ourInput.substring(0, 100));
console.log('Last 100 chars:', ourInput.substring(ourInput.length - 100));
console.log('Full:', ourInput);
console.log('\n');

// Generate sign
const ourSign = generateSign(OUR_PARAMS);
console.log('Our Generated Sign:');
console.log(ourSign);
console.log('\n');

console.log('========================================');
console.log('EXPECTED INPUT FROM APP:');
console.log('========================================');
console.log('When you browse the app, Frida will capture the ACTUAL input.');
console.log('Compare it with our input above to find the difference!');
console.log('\n');
console.log('Possible differences to check:');
console.log('1. Path format (/home/index vs /hwycclientreels/home/index)');
console.log('2. Parameter order');
console.log('3. Missing or extra parameters');
console.log('4. Encoding differences');
console.log('========================================\n');
