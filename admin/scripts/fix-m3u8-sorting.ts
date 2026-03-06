import { ListObjectsV2Command, PutObjectCommand } from '@aws-sdk/client-s3';
import { r2Client, R2_BUCKET, getR2PublicUrl } from '../config/r2';

const R2_PUBLIC_BASE = 'https://pub-shortlovers.r2.dev';

interface EpisodeSegments {
    folderPath: string;
    segments: string[];
}

/**
 * Generate M3U8 playlist content for HLS streaming with CORRECT sorting
 */
function generateM3U8(segments: string[], duration: number = 10): string {
    // CRITICAL FIX: Use numeric sort (1, 2, 10) instead of alphabetical (1, 10, 2)
    const sortedSegments = [...segments].sort((a, b) => {
        // Extract filename from path
        const fileA = a.split('/').pop() || '';
        const fileB = b.split('/').pop() || '';

        // Use localeCompare with numeric option for "Natural Sort"
        return fileA.localeCompare(fileB, undefined, { numeric: true, sensitivity: 'base' });
    });

    let m3u8 = '#EXTM3U\n';
    m3u8 += '#EXT-X-VERSION:3\n';
    m3u8 += `#EXT-X-TARGETDURATION:${duration}\n`;
    m3u8 += '#EXT-X-MEDIA-SEQUENCE:0\n';
    m3u8 += '#EXT-X-PLAYLIST-TYPE:VOD\n\n';

    for (const segment of sortedSegments) {
        // Relative path (just filename) - safer and domain-agnostic
        m3u8 += `#EXTINF:${duration}.0,\n`;
        m3u8 += `${segment.split('/').pop()}\n`;
    }

    m3u8 += '#EXT-X-ENDLIST\n';
    return m3u8;
}

async function fixAllocatedSorting() {
    console.log('🔧 Starting M3U8 Sorting Fix...');
    console.log(`🪣 Bucket: ${R2_BUCKET}`);

    const episodeMap = new Map<string, EpisodeSegments>();
    let continuationToken: string | undefined;
    let totalObjects = 0;

    // 1. Scan all objects
    console.log('\n🔍 Scanning bucket for .ts segments...');
    do {
        const command = new ListObjectsV2Command({
            Bucket: R2_BUCKET,
            MaxKeys: 1000,
            ContinuationToken: continuationToken,
        });

        const response = await r2Client.send(command);
        totalObjects += response.Contents?.length || 0;

        for (const item of response.Contents || []) {
            if (!item.Key || !item.Key.endsWith('.ts')) continue;

            const parts = item.Key.split('/');
            // Expecting: DramaName/EpisodeName/segment.ts
            if (parts.length < 3) continue;

            const folderPath = parts.slice(0, 2).join('/');

            if (!episodeMap.has(folderPath)) {
                episodeMap.set(folderPath, {
                    folderPath,
                    segments: []
                });
            }

            episodeMap.get(folderPath)!.segments.push(item.Key);
        }

        continuationToken = response.NextContinuationToken;
        if (totalObjects % 1000 === 0) process.stdout.write('.');

    } while (continuationToken);

    console.log(`\n\nfound ${episodeMap.size} episodes with video segments.`);

    // 2. Process each episode
    let fixedCount = 0;
    let errorCount = 0;

    for (const [folder, data] of episodeMap) {
        try {
            // Generate NEW corrected M3U8
            const m3u8Content = generateM3U8(data.segments);
            const playlistKey = `${folder}/playlist.m3u8`;

            // Upload to R2 (Overwrite existing)
            await r2Client.send(new PutObjectCommand({
                Bucket: R2_BUCKET,
                Key: playlistKey,
                Body: m3u8Content,
                ContentType: 'application/vnd.apple.mpegurl',
                CacheControl: 'no-cache', // Important to ensure players don't cache bad playlist
            }));

            fixedCount++;
            if (fixedCount % 10 === 0) console.log(`✅ Fixed ${fixedCount} playlists...`);

        } catch (error: any) {
            console.error(`❌ Error processing ${folder}: ${error.message}`);
            errorCount++;
        }
    }

    console.log('\n' + '='.repeat(50));
    console.log(`🎉 COMPLETED`);
    console.log(`✅ Fixed: ${fixedCount}`);
    console.log(`❌ Errors: ${errorCount}`);
    console.log('='.repeat(50));
}

fixAllocatedSorting()
    .then(() => process.exit(0))
    .catch((err) => {
        console.error(err);
        process.exit(1);
    });
