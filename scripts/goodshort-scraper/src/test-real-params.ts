/**
 * Test API with COMPLETE Real Device Parameters
 */

import { GoodShortAPIClient } from './api/goodshort-client';

// COMPLETE device parameters - ALL extracted!
const DEVICE_PARAMS = {
    gaid: '3a527bd0-4a98-47e7-ac47-f592c165d870',
    androidId: 'ffffffffcf4ce71dcf4ce71d00000000',
    userToken: '', // Empty for public endpoints
    appSignatureMD5: 'CA28D371148D19831C9995293CD1CACE' // ✅ EXTRACTED!
};

async function testWithRealParams() {
    console.log('========================================');
    console.log('Testing API with COMPLETE Parameters');
    console.log('========================================\n');

    console.log('Device Config:');
    console.log(JSON.stringify(DEVICE_PARAMS, null, 2));
    console.log('\n');

    const client = new GoodShortAPIClient(DEVICE_PARAMS);

    // Test 1: Home/Discover
    console.log('Test 1: Fetching home data...');
    try {
        const homeData = await client.getHomeData();
        console.log('✅ SUCCESS! Home data retrieved!');
        console.log('Response preview:', JSON.stringify(homeData, null, 2).substring(0, 500));
        console.log('\n');
    } catch (error: any) {
        console.log('❌ FAILED');
        console.log('Status:', error.response?.status);
        console.log('Error:', JSON.stringify(error.response?.data, null, 2));
        console.log('\n');
    }

    // Test 2: Specific Drama (dari capture sebelumnya)
    const testBookId = '31000908479'; // Drama yang ter-capture tadi
    console.log(`Test 2: Fetching drama details (ID: ${testBookId})...`);
    try {
        const dramaData = await client.getDrama(testBookId);
        console.log('✅ SUCCESS! Drama data retrieved!');
        console.log('Drama:', JSON.stringify(dramaData, null, 2).substring(0, 500));
        console.log('\n');
    } catch (error: any) {
        console.log('❌ FAILED');
        console.log('Status:', error.response?.status);
        console.log('Error:', JSON.stringify(error.response?.data, null, 2));
        console.log('\n');
    }

    // Test 3: Chapter List
    console.log(`Test 3: Fetching chapter list (ID: ${testBookId})...`);
    try {
        const chapters = await client.getChapterList(testBookId);
        console.log('✅ SUCCESS! Chapter list retrieved!');
        console.log('Chapters:', JSON.stringify(chapters, null, 2).substring(0, 500));
        console.log('\n');

        // If successful, extract video URLs
        if (chapters && chapters.data && chapters.data.list) {
            console.log(`Found ${chapters.data.list.length} chapters!`);
            console.log('Sample chapter info:');
            console.log(JSON.stringify(chapters.data.list[0], null, 2));
        }
    } catch (error: any) {
        console.log('❌ FAILED');
        console.log('Status:', error.response?.status);
        console.log('Error:', JSON.stringify(error.response?.data, null, 2));
        console.log('\n');
    }

    console.log('========================================');
    console.log('Test Complete');
    console.log('========================================\n');

    console.log('If all tests passed, API client is fully functional!');
    console.log('We can now scrape dramas directly via API! 🎉\n');
}

testWithRealParams().catch(console.error);
