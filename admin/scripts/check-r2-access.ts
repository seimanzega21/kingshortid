import { GetObjectCommand, HeadBucketCommand } from '@aws-sdk/client-s3';
import { r2Client, R2_BUCKET } from '../config/r2';

async function checkR2Access() {
    console.log('🔍 Checking R2 Bucket Access...\n');
    console.log('='.repeat(60));

    const accountId = process.env.R2_ENDPOINT?.match(/([a-f0-9]+)\.r2\.cloudflarestorage\.com/)?.[1];
    console.log(`📦 Bucket: ${R2_BUCKET}`);
    console.log(`🔑 Account ID: ${accountId || 'Unknown'}`);
    console.log('='.repeat(60));

    // Test 1: Check bucket access via API
    console.log('\n1️⃣ Testing API Access...');
    try {
        const command = new HeadBucketCommand({ Bucket: R2_BUCKET });
        await r2Client.send(command);
        console.log('   ✅ API Access: OK (credentials work)');
    } catch (error: any) {
        console.log('   ❌ API Access: FAILED');
        console.log(`   Error: ${error.message}`);
    }

    // Test 2: Get a sample file to check if it exists
    console.log('\n2️⃣ Testing File Access...');
    const testKey = '[sulih_suara]_suamiku_ternyata_ceo/[sulih_suara]_suamiku_ternyata_ceo_ep_1/cover.jpg';
    try {
        const command = new GetObjectCommand({
            Bucket: R2_BUCKET,
            Key: testKey,
        });
        const response = await r2Client.send(command);
        console.log('   ✅ File Access: OK');
        console.log(`   File Size: ${response.ContentLength} bytes`);
        console.log(`   Content-Type: ${response.ContentType}`);
    } catch (error: any) {
        console.log('   ❌ File Access: FAILED');
        console.log(`   Error: ${error.message}`);
    }

    // Test 3: Check public URL access
    console.log('\n3️⃣ Testing Public URL Access...');

    // Possible public URL formats
    const publicUrls = [
        `https://pub-${accountId}.r2.dev/${testKey}`,
        `https://${R2_BUCKET}.${accountId}.r2.cloudflarestorage.com/${testKey}`,
    ];

    for (const url of publicUrls) {
        try {
            console.log(`\n   Testing: ${url.substring(0, 60)}...`);
            const response = await fetch(url, { method: 'HEAD' });

            if (response.ok) {
                console.log(`   ✅ PUBLIC ACCESS WORKS!`);
                console.log(`   Status: ${response.status}`);
                console.log(`   Content-Type: ${response.headers.get('content-type')}`);
                console.log(`\n   🎉 Use this base URL: ${url.replace(testKey, '')}`);
            } else {
                console.log(`   ❌ Status: ${response.status} ${response.statusText}`);
            }
        } catch (error: any) {
            console.log(`   ❌ Error: ${error.message}`);
        }
    }

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('📋 R2 BUCKET CONFIGURATION GUIDE');
    console.log('='.repeat(60));
    console.log(`
Untuk mengaktifkan akses publik R2:

1. Buka Cloudflare Dashboard → R2
2. Pilih bucket "${R2_BUCKET}"
3. Klik "Settings" tab
4. Di bawah "Public Access", klik "Allow Access"
5. Salin "Public Bucket URL" yang diberikan
6. Update .env dengan URL tersebut:
   R2_PUBLIC_URL="https://pub-xxxxx.r2.dev"

Atau gunakan Custom Domain untuk URL yang lebih pendek.
`);
}

checkR2Access()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error('Error:', error);
        process.exit(1);
    });
