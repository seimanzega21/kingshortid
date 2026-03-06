/**
 * Brute force test - try all path variations with real API
 */

import axios from 'axios';
import { generateSign } from './sign-generator';

const PARAMS = {
    gaid: '3a527bd0-4a98-47e7-ac47-f592c165d870',
    androidId: 'ffffffffcf4ce71dcf4ce71d00000000',
    userToken: '',
    appSignatureMD5: 'CA28D371148D19831C9995293CD1CACE'
};

async function testPathVariation(pathForSign: string, pathForURL: string) {
    const timestamp = Date.now().toString();

    const sign = generateSign({
        timestamp,
        path: pathForSign,
        ...PARAMS
    });

    try {
        const response = await axios.post(
            `https://api-akm.goodreels.com/hwycclientreels${pathForURL}?timestamp=${timestamp}`,
            {
                pageNo: 1,
                pageSize: 12,
                channelType: 3,
                vipBookEnable: true,
                channelId: -3
            },
            {
                headers: {
                    'sign': sign,
                    'User-Agent': 'okhttp/4.10.0',
                    'Content-Type': 'application/json'
                }
            }
        );

        return { success: response.data.success, message: response.data.message, data: response.data };
    } catch (error: any) {
        return { success: false, message: error.response?.data?.message || error.message };
    }
}

async function main() {
    console.log('========================================');
    console.log('Brute Force Path Variation Test');
    console.log('========================================\n');

    const variations = [
        { signPath: '/home/index', urlPath: '/home/index', desc: 'Both relative' },
        { signPath: '/hwycclientreels/home/index', urlPath: '/home/index', desc: 'Sign full, URL relative' },
        { signPath: 'home/index', urlPath: '/home/index', desc: 'Sign no slash, URL relative' },
        { signPath: '/home/index', urlPath: '/hwycclientreels/home/index', desc: 'Sign relative, URL full' },
        { signPath: '/hwycclientreels/home/index', urlPath: '/hwycclientreels/home/index', desc: 'Both full' }
    ];

    for (let i = 0; i < variations.length; i++) {
        const v = variations[i];
        console.log(`Test ${i + 1}: ${v.desc}`);
        console.log(`  Sign path: "${v.signPath}"`);
        console.log(`  URL path: "${v.urlPath}"`);

        const result = await testPathVariation(v.signPath, v.urlPath);

        if (result.success === true) {
            console.log('  ✅ SUCCESS! This is the correct variation!');
            console.log('  Response:', JSON.stringify(result.data, null, 2).substring(0, 200));
            console.log('\n🎉 FOUND IT! Use this configuration!\n');
            break;
        } else {
            console.log(`  ❌ Failed: ${result.message}`);
        }
        console.log('');

        // Small delay between requests
        await new Promise(resolve => setTimeout(resolve, 500));
    }

    console.log('========================================');
    console.log('Test Complete');
    console.log('========================================');
}

main().catch(console.error);
