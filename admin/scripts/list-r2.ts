import { ListObjectsV2Command } from '@aws-sdk/client-s3';
import { r2Client, R2_BUCKET } from '../config/r2';

async function listRoot() {
    console.log(`🔍 Listing root of bucket ${R2_BUCKET}...`);
    try {
        const command = new ListObjectsV2Command({
            Bucket: R2_BUCKET,
            MaxKeys: 20,
            Delimiter: '/'
        });
        const response = await r2Client.send(command);

        console.log('--- Common Prefixes (Folders) ---');
        response.CommonPrefixes?.forEach(p => console.log(p.Prefix));

        console.log('\n--- Object Keys ---');
        response.Contents?.forEach(c => console.log(c.Key));

    } catch (error: any) {
        console.error('Error:', error.message);
    }
}

listRoot();
