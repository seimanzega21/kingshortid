/**
 * Test API with Multiple APK Signature MD5 Attempts
 * 
 * Since extracting the exact MD5 is difficult, we'll try:
 * 1. Empty string (maybe it's not validated)
 * 2. Common placeholder values
 * 3. If those fail, we know we need the exact value
 */

import { GoodShortAPIClient } from './api/goodshort-client';

const DEVICE_PARAMS = {
    gaid: '3a527bd0-4a98-47e7-ac47-f592c165d870',
    androidId: 'ffffffffcf4ce71dcf4ce71d00000000',
    userToken: '' // Try without token first
};

async function testWithVariousSignatures() {
    console.log('========================================');
    console.log('Testing API with Various APK Signatures');
    console.log('========================================\n');

    const testSignatures = [
        { name: 'Empty String', value: '' },
        { name: 'Single Zero', value: '0' },
        { name: 'All Zeros (32 chars)', value: '0'.repeat(32) },
        { name: 'All Fs (32 chars)', value: 'F'.repeat(32) },
        { name: 'Typical MD5 Pattern', value: 'A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6' }
    ];

    for (const sig of testSignatures) {
        console.log(`\n--- Testing: ${sig.name} ---`);
        console.log(`Value: "${sig.value}"`);

        const client = new GoodShortAPIClient({
            ...DEVICE_PARAMS,
            appSignatureMD5: sig.value
        });

        try {
            console.log('Calling /v1/home...');
            const result = await client.getHomeData();

            console.log('✅ SUCCESS!');
            console.log(`Signature "${sig.name}" works!`);
            console.log('Response:', JSON.stringify(result, null, 2).substring(0, 200));

            // If successful, save this config
            console.log('\n🎉 FOUND WORKING SIGNATURE!');
            console.log('Config:', JSON.stringify({ ...DEVICE_PARAMS, appSignatureMD5: sig.value }, null, 2));
            break;

        } catch (error: any) {
            console.log(`❌ Failed (${error.response?.status || error.code})`);
            if (error.response?.status === 403) {
                console.log('   → Still getting 403, signature not accepted');
            } else if (error.response?.status) {
                console.log('   → Different error:', error.response.status, error.response.data);
            }
        }
    }

    console.log('\n========================================');
    console.log('Test Complete');
    console.log('========================================\n');

    console.log('If all failed, we need the EXACT APK signature MD5.');
    console.log('Alternative: Use captured API data from metadata capture instead.\n');
}

testWithVariousSignatures().catch(console.error);
