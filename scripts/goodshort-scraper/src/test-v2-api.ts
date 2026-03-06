/**
 * Test V2 Sign Generator with LIVE API call
 */

import { generateSignV2 } from './sign-generator-v2';
import axios from 'axios';

async function testLiveAPI() {
    console.log('='.repeat(60));
    console.log('TESTING V2 SIGN GENERATOR WITH LIVE API');
    console.log('='.repeat(60));

    const timestamp = Date.now().toString();

    const body = {
        pageNo: 1,
        pageSize: 12,
        channelType: 3,
        vipBookEnable: true,
        channelId: -3
    };

    // Device params from captured session
    const gaid = '3a527bd0-4a98-47e7-ac47-f592c165d870';
    const androidId = 'ffffffffcf4ce71dcf4ce71d00000000';
    const userToken = 'Bearer ZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SnlaV2RwYzNSbGNsUjVjR1VpT2lKUVJWSk5RVTVGVGxRaUxDSjFjMlZ5U1dRaU9qRTJNREExT0RReE4zMC5XYzA4LXpEOUxuaHBCREJkRENrMDBPQWxiLUtCa3ZKek9jbmg2Ump6MENF';

    // Generate sign using V2 (corrected format)
    const sign = generateSignV2({
        timestamp,
        body,
        gaid,
        androidId,
        userToken
    });

    console.log('\n=== Making API Call ===');

    const url = `https://api-akm.goodreels.com/hwycclientreels/home/index?timestamp=${timestamp}`;

    const headers = {
        'sign': sign,
        'Authorization': userToken,
        'deviceId': gaid,
        'androidId': androidId,
        'pname': 'com.newreading.goodreels',
        'platform': 'ANDROID',
        'appVersion': '2782078',
        'Content-Type': 'application/json; charset=UTF-8',
        'User-Agent': 'okhttp/4.10.0',
        'scWidth': '1080',
        'scHeight': '2072',
        'language': 'en',
        'os': '11'
    };

    try {
        console.log('URL:', url);
        console.log('Body:', JSON.stringify(body));

        const response = await axios.post(url, body, { headers, timeout: 15000 });

        console.log('\nStatus:', response.status);
        console.log('Success:', response.data.success);

        if (response.data.success) {
            console.log('\n!!! SUCCESS !!!');
            const books = response.data.data?.bookList || [];
            console.log(`Got ${books.length} books!`);

            if (books.length > 0) {
                console.log('\nFirst 3 books:');
                books.slice(0, 3).forEach((book: any) => {
                    console.log(`  - ${book.bookName}`);
                });
            }
        } else {
            console.log('\nFailed:', response.data.message);
            console.log('Full response:', JSON.stringify(response.data));
        }

    } catch (error: any) {
        console.log('\nError:', error.message);
        if (error.response) {
            console.log('Response:', error.response.data);
        }
    }

    console.log('\n' + '='.repeat(60));
}

testLiveAPI();
