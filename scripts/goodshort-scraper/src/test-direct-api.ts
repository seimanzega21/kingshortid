/**
 * Direct API Test - No Sign Required?
 * Let's test if API works WITHOUT sign header
 */

import axios from 'axios';

const BASE_URL = 'https://api-akm.goodreels.com/hwyclientreels';

async function testDirectAPI() {
    console.log('🧪 Testing GoodShort API without authentication...\n');

    const tests = [
        {
            name: 'Get Drama Detail',
            url: `${BASE_URL}/book/detail`,
            params: { bookId: '31000908479' }
        },
        {
            name: 'Get Chapter List',
            url: `${BASE_URL}/chapter/list`,
            params: { bookId: '31000908479' }
        },
        {
            name: 'Get Drama List',
            url: `${BASE_URL}/book/list`,
            params: { page: 1 }
        }
    ];

    for (const test of tests) {
        console.log(`\n${'='.repeat(70)}`);
        console.log(`Testing: ${test.name}`);
        console.log(`URL: ${test.url}`);
        console.log(`Params: ${JSON.stringify(test.params)}`);
        console.log('='.repeat(70));

        try {
            const response = await axios.get(test.url, {
                params: test.params,
                headers: {
                    'User-Agent': 'GoodReels/2.7.8 (Android)',
                    'Accept': 'application/json'
                },
                timeout: 10000
            });

            console.log(`✅ SUCCESS! Status: ${response.status}`);
            console.log('Response:', JSON.stringify(response.data, null, 2).substring(0, 500));

            if (response.data && response.data.data) {
                console.log('\n📦 Data structure looks valid!');
                if (Array.isArray(response.data.data)) {
                    console.log(`   Array with ${response.data.data.length} items`);
                } else {
                    console.log(`   Object with keys: ${Object.keys(response.data.data).join(', ')}`);
                }
            }

        } catch (error: any) {
            console.log(`❌ FAILED: ${error.message}`);
            if (error.response) {
                console.log(`   Status: ${error.response.status}`);
                console.log(`   Data: ${JSON.stringify(error.response.data)}`);
            }
        }
    }

    console.log(`\n${'='.repeat(70)}`);
    console.log('🎯 CONCLUSION:');
    console.log('If you see SUCCESS above - WE CAN USE API WITHOUT SIGN!');
    console.log('If all FAILED - we need sign generation (back to reverse engineering)');
    console.log('='.repeat(70) + '\n');
}

testDirectAPI().catch(console.error);
