/**
 * Test with extracted user token from Authorization header
 */

import { generateSign } from './sign-generator';
import axios from 'axios';

// From captured headers
const BEARER_TOKEN_BASE64 = "ZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SnlaV2RwYzNSbGNsUjVjR1VpT2lKUVJWSk5RVTVGVGxRaUxDSjFjMlZ5U1dRaU9qRTJNREExT0RReE4zMC5XYzA4LXpEOUxuaHBCREJkRENrMDBPQWxiLUtCa3ZKek9jbmg2Ump6MENF";

const PARAMS = {
    gaid: '3a527bd0-4a98-47e7-ac47-f592c165d870',
    androidId: 'ffffffffcf4ce71dcf4ce71d00000000',
    appSignatureMD5: 'CA28D371148D19831C9995293CD1CACE'
};

async function testWithUserToken() {
    console.log('========================================');
    console.log('Testing with User Token from Bearer');
    console.log('========================================\n');

    const timestamp = Date.now().toString();
    const path = '/home/index';

    // Test with bearer token as userToken
    console.log('Test 1: Using full bearer token base64 as userToken...');
    const sign1 = generateSign({
        timestamp,
        path,
        ...PARAMS,
        userToken: BEARER_TOKEN_BASE64
    });

    console.log('Generated sign (first 60):', sign1.substring(0, 60));

    try {
        const response = await axios.post(
            `https://api-akm.goodreels.com/hwycclientreels${path}?timestamp=${timestamp}`,
            {
                pageNo: 1,
                pageSize: 12,
                channelType: 3,
                vipBookEnable: true,
                channelId: -3
            },
            {
                headers: {
                    'sign': sign1,
                    'Authorization': `Bearer ${BEARER_TOKEN_BASE64}`,
                    'User-Agent': 'okhttp/4.10.0',
                    'Content-Type': 'application/json'
                }
            }
        );

        if (response.data.success) {
            console.log('✅ SUCCESS!!!');
            console.log('Response:', JSON.stringify(response.data, null, 2).substring(0, 300));
        } else {
            console.log('❌ Failed:', response.data.message);
        }
    } catch (error: any) {
        console.log('❌ Error:', error.response?.data?.message || error.message);
    }

    console.log('\n========================================\n');
}

testWithUserToken().catch(console.error);
