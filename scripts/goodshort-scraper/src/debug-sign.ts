/**
 * Debug Sign Generation
 * Test various combinations to see what works
 */

import { generateSign } from './sign-generator';

const PARAMS = {
    gaid: '3a527bd0-4a98-47e7-ac47-f592c165d870',
    androidId: 'ffffffffcf4ce71dcf4ce71d00000000',
    appSignatureMD5: 'CA28D371148D19831C9995293CD1CACE',
    userToken: '',
    packageName: 'com.newreading.goodreels'
};

console.log('Testing Sign Generation Variations...\n');

const path = '/v1/home';
const timestamp = Date.now().toString();

console.log('Test Parameters:');
console.log('Path:', path);
console.log('Timestamp:', timestamp);
console.log('\n');

// Test 1: As implemented
console.log('Test 1: Standard implementation');
const sign1 = generateSign(path, timestamp, PARAMS);
console.log('Sign:', sign1.substring(0, 60) + '...');
console.log('\n');

// Test 2: With lowercase MD5
console.log('Test 2: Lowercase MD5');
const sign2 = generateSign(path, timestamp, {
    ...PARAMS,
    appSignatureMD5: PARAMS.appSignatureMD5.toLowerCase()
});
console.log('Sign:', sign2.substring(0, 60) + '...');
console.log('\n');

// Test 3: Empty MD5
console.log('Test 3: Empty MD5');
const sign3 = generateSign(path, timestamp, {
    ...PARAMS,
    appSignatureMD5: ''
});
console.log('Sign:', sign3.substring(0, 60) + '...');
console.log('\n');

// Test 4: Check input string format
console.log('Test 4: Input string format');
const inputString = `${path}${timestamp}${PARAMS.gaid}${PARAMS.androidId}${PARAMS.userToken}${PARAMS.appSignatureMD5}${PARAMS.packageName}`;
console.log('Input length:', inputString.length);
console.log('Input preview:', inputString.substring(0, 200) + '...');
console.log('\n');

console.log('Perhaps the API needs additional headers or different parameter order?');
console.log('Let me check the actual sign from Frida capture...\n');
