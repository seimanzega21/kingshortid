import 'dotenv/config';
import { ListObjectsV2Command } from '@aws-sdk/client-s3';
import { r2Client, R2_BUCKET } from '../config/r2';

async function analyzeBroadly() {
    console.log(`🔍 Analyzing broad structure...`);

    try {
        const command = new ListObjectsV2Command({
            Bucket: R2_BUCKET,
            MaxKeys: 1000,
        });

        const response = await r2Client.send(command);

        if (!response.Contents) {
            console.log('No contents found.');
            return;
        }

        // Check for m3u8 files
        const m3u8 = response.Contents.filter(item => item.Key?.endsWith('.m3u8'));
        console.log(`\n📺 Found ${m3u8.length} .m3u8 files in first 1000 objects:`);
        m3u8.slice(0, 10).forEach(f => console.log(` - ${f.Key}`));

        // Check for mp4 files
        const mp4 = response.Contents.filter(item => item.Key?.endsWith('.mp4'));
        console.log(`\n🎥 Found ${mp4.length} .mp4 files in first 1000 objects:`);
        mp4.slice(0, 10).forEach(f => console.log(` - ${f.Key}`));

        // Check for ANY file with 'playlist' or 'index' or 'master' in name
        const matches = response.Contents.filter(item =>
            item.Key?.includes('playlist') ||
            item.Key?.includes('index') ||
            item.Key?.includes('master')
        );
        console.log(`\n📄 Found ${matches.length} potential playlist files:`);
        matches.slice(0, 10).forEach(f => console.log(` - ${f.Key}`));


    } catch (error) {
        console.error(error);
    }
}

analyzeBroadly();
