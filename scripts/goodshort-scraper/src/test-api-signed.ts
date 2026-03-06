/**
 * Test GoodShort API with RSA-SHA256 Sign Generation
 * 
 * Tests various parameter configurations to determine requirements
 */

import { GoodShortAPIClient } from './api/goodshort-client';
import { testSignGeneration } from './sign-generator';

async function testAPI() {
    console.log('========================================');
    console.log('GoodShort API Testing - RSA Sign Gen');
    console.log('========================================\n');

    // Test 1: Sign generation test
    console.log('Test 1: Testing RSA-SHA256 sign generation...');
    testSignGeneration();
    console.log('\n');

    // Test 2: Empty parameters
    console.log('Test 2: API call with EMPTY parameters...');
    const clientEmpty = new GoodShortAPIClient({
        gaid: '',
        androidId: '',
        userToken: '',
        appSignatureMD5: ''
    });

    try {
        console.log('Fetching home data...');
        const homeData = await clientEmpty.getHomeData();
        console.log('✅ SUCCESS! API accepts empty parameters!');
        console.log('Response:', JSON.stringify(homeData, null, 2).substring(0, 500));
    } catch (error: any) {
        console.log('❌ FAILED with empty parameters');
        console.log('Status:', error.response?.status);
        console.log('Error:', error.response?.data || error.message);
    }
    console.log('\n');

    // Test 3: Dummy parameters
    console.log('Test 3: API call with DUMMY parameters...');
    const clientDummy = new GoodShortAPIClient({
        gaid: '00000000-0000-0000-0000-000000000000',
        androidId: 'ffffffffffffffff',
        userToken: '',
        appSignatureMD5: 'A1B2C3D4E5F6G7H8'
    });

    try {
        console.log('Fetching home data...');
        const homeData = await clientDummy.getHomeData();
        console.log('✅ SUCCESS! API accepts dummy parameters!');
        console.log('Response:', JSON.stringify(homeData, null, 2).substring(0, 500));
    } catch (error: any) {
        console.log('❌ FAILED with dummy parameters');
        console.log('Status:', error.response?.status);
        console.log('Error:', error.response?.data || error.message);
    }
    console.log('\n');

    // Test 4: Specific drama
    console.log('Test 4: Testing drama endpoint...');
    const testBookId = '5178178';

    try {
        console.log(`Fetching drama ${testBookId}...`);
        const dramaData = await clientEmpty.getDrama(testBookId);
        console.log('✅ SUCCESS! Drama endpoint works!');
        console.log('Response:', JSON.stringify(dramaData, null, 2).substring(0, 500));
    } catch (error: any) {
        console.log('❌ FAILED');
        console.log('Status:', error.response?.status);
        console.log('Error:', error.response?.data || error.message);
    }
    console.log('\n');

    console.log('========================================');
    console.log('TO EXTRACT REAL DEVICE PARAMETERS:');
    console.log('========================================');
    console.log('Run: start-extract-params.bat');
    console.log('Then use the app to capture real values');
    console.log('========================================\n');
}

// Run tests
testAPI().catch(console.error);
