import { ListObjectsV2Command, GetObjectCommand, PutObjectCommand } from '@aws-sdk/client-s3';
import { r2Client, R2_BUCKET } from '../config/r2';
import mediainfo from 'mediainfo.js';
import fs from 'fs';
import path from 'path';
import { Readable } from 'stream';
import { finished } from 'stream/promises';

// Target specific drama folder
// Scan all folders (Global Fix)
async function main() {
    console.log('🔍 Listing ALL objects in bucket (finding episodes)...');

    // 1. List all objects to find episode folders
    // Note: R2 integeration with list-objects-v2 is standard. 
    // We'll list everything and extract unique prefixes ending in `_ep_\d+/`
    let isTruncated = true;
    let continuationToken: string | undefined = undefined;
    const allKeys: string[] = [];

    while (isTruncated) {
        const response = await r2Client.send(new ListObjectsV2Command({
            Bucket: R2_BUCKET,
            ContinuationToken: continuationToken
        }));

        response.Contents?.forEach(c => {
            if (c.Key) allKeys.push(c.Key);
        });

        isTruncated = response.IsTruncated || false;
        continuationToken = response.NextContinuationToken;
        console.log(`Fetched ${allKeys.length} keys...`);
    }

    // 2. Identify episode folders
    const episodeFolders = new Set<string>();
    const folderRegex = /^(.+?_ep_\d+)\//; // Matches "drama_name_ep_1/"

    allKeys.forEach(key => {
        const match = key.match(folderRegex);
        if (match) {
            episodeFolders.add(match[1] + '/');
        }
    });

    const folders = Array.from(episodeFolders);
    console.log(`\nFound ${folders.length} episode folders to process.\n`);

    // 3. Process each folder
    for (const folder of folders) {
        console.log(`👉 Processing: ${folder}`);

        // internal logic to process ONE folder (extracted here for reuse)
        await processFolder(folder, allKeys);
    }

    console.log('\n✅ GLOBAL FIX COMPLETE!');
}

async function processFolder(folderPrefix: string, allKeys: string[]) {
    // Filter keys belonging to this folder from our big list (optimization)
    const segments = allKeys
        .filter(k => k.startsWith(folderPrefix) && k.endsWith('.ts'))
        .sort((a, b) => {
            const numA = parseInt(a.match(/shortlovers_(\d+)/)?.[1] || '0');
            const numB = parseInt(b.match(/shortlovers_(\d+)/)?.[1] || '0');
            return numA - numB;
        });

    if (segments.length === 0) {
        console.log('   ⚠️ No segments found, skipping.');
        return;
    }

    console.log(`   Found ${segments.length} segments.`);
    let m3u8Content = `#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:10\n#EXT-X-MEDIA-SEQUENCE:0\n#EXT-X-PLAYLIST-TYPE:VOD\n\n`;
    let maxDuration = 0;

    for (const segKey of segments) {
        const filename = path.basename(segKey);
        const localPath = await downloadToTemp(segKey, filename); // Uses cached check

        try {
            const duration = await getDuration(localPath);
            // console.log(`   - ${filename}: ${duration.toFixed(3)}s`);
            if (duration > maxDuration) maxDuration = duration;
            m3u8Content += `#EXTINF:${duration.toFixed(6)},\n${filename}\n`;
        } catch (e) {
            console.error(`   ❌ Error analyzing ${filename}, using default 10s`);
            m3u8Content += `#EXTINF:10.000000,\n${filename}\n`;
        }
    }

    m3u8Content += `#EXT-X-ENDLIST\n`;

    const targetDur = Math.ceil(maxDuration || 10);
    m3u8Content = m3u8Content.replace('#EXT-X-TARGETDURATION:10', `#EXT-X-TARGETDURATION:${targetDur}`);

    // console.log('   🚀 Uploading fixed playlist...');
    await r2Client.send(new PutObjectCommand({
        Bucket: R2_BUCKET,
        Key: `${folderPrefix}playlist.m3u8`,
        Body: m3u8Content,
        ContentType: 'application/vnd.apple.mpegurl',
        CacheControl: 'no-cache, no-store'
    }));
    console.log('   ✅ Fixed.');
}

main().catch(console.error);
