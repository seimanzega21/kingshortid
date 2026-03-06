/**
 * Test different path variations to find correct format
 */

import { generateSign } from './sign-generator';

const BASE_PARAMS = {
    timestamp: '1769855063192',
    gaid: '3a527bd0-4a98-47e7-ac47-f592c165d870',
    androidId: 'ffffffffcf4ce71dcf4ce71d00000000',
    userToken: '',
    appSignatureMD5: 'CA28D371148D19831C9995293CD1CACE'
};

console.log('Testing Different Path Formats...\n');

const pathVariations = [
    '/home/index',
    '/hwycclientreels/home/index',
    'home/index',
    '/hwyclientreels/home/index',
    'hwycclientreels/home/index'
];

pathVariations.forEach((path, i) => {
    console.log(`${i + 1}. Path: "${path}"`);

    const input =
        path +
        BASE_PARAMS.timestamp +
        BASE_PARAMS.gaid +
        BASE_PARAMS.androidId +
        BASE_PARAMS.userToken +
        BASE_PARAMS.appSignatureMD5 +
        'com.newreading.goodreels';

    console.log('   Input length:', input.length);
    console.log('   First 80 chars:', input.substring(0, 80));

    try {
        const sign = generateSign({ ...BASE_PARAMS, path });
        console.log('   Sign (first 40):', sign.substring(0, 40));
    } catch (e) {
        console.log('   Error:', e.message);
    }
    console.log('');
});

console.log('========================================');
console.log('Analysis from captured headers:');
console.log('========================================');
console.log('Base URL: https://api-akm.goodreels.com/hwycclientreels');
console.log('Sample endpoint: /home/index?timestamp=...');
console.log('');
console.log('This suggests path for signing might be:');
console.log('  Option 1: /home/index (relative to base)');
console.log('  Option 2: /hwycclientreels/home/index (full path)');
console.log('');
console.log('Need to capture actual app behavior to confirm!');
