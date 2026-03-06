const { S3Client, ListObjectsV2Command } = require('@aws-sdk/client-s3');
require('dotenv').config();

const s3 = new S3Client({
    region: 'auto',
    endpoint: process.env.R2_ENDPOINT,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
    },
});
const BUCKET = process.env.R2_BUCKET_NAME;

async function listPrefixes(prefix = '') {
    const slugs = new Set();
    let token;
    do {
        const res = await s3.send(new ListObjectsV2Command({
            Bucket: BUCKET, Prefix: prefix, Delimiter: '/', ContinuationToken: token,
        }));
        for (const cp of (res.CommonPrefixes || [])) {
            slugs.add(cp.Prefix);
        }
        token = res.NextContinuationToken;
    } while (token);
    return [...slugs];
}

async function main() {
    console.log('=== dramas/ ===');
    const dramas = await listPrefixes('dramas/');
    console.log(`  Found ${dramas.length} items`);
    for (const d of dramas.slice(0, 10)) console.log(`    ${d}`);
    if (dramas.length > 10) console.log(`    ... and ${dramas.length - 10} more`);

    console.log('\n=== microdrama/ ===');
    const micro = await listPrefixes('microdrama/');
    console.log(`  Found ${micro.length} items`);
    for (const m of micro.slice(0, 10)) console.log(`    ${m}`);
    if (micro.length > 10) console.log(`    ... and ${micro.length - 10} more`);

    console.log(`\n=== Total Missing ===`);
    console.log(`  dramas/: ${dramas.length}`);
    console.log(`  microdrama/: ${micro.length}`);
    console.log(`  Combined: ${dramas.length + micro.length}`);
}

main().catch(console.error);
