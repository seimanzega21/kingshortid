const { execSync } = require('child_process');
const fs = require('fs');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { PrismaClient } = require('@prisma/client');
require('dotenv').config();

const prisma = new PrismaClient();

const s3 = new S3Client({
    region: 'auto',
    endpoint: process.env.R2_ENDPOINT,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
    },
});

const BUCKET = process.env.R2_BUCKET_NAME;
const R2_PUBLIC_URL = process.env.R2_PUBLIC_URL || 'https://stream.shortlovers.id';
const DRAMA_ID = 'cmleey1t70622hx5eskusjzp9';
const SLUG = 'levelku-9999-tetua-baru-100';

async function uploadToR2(filePath, s3Key) {
    const fileStream = fs.createReadStream(filePath);
    await s3.send(new PutObjectCommand({
        Bucket: BUCKET,
        Key: s3Key,
        Body: fileStream,
        ContentType: 'video/mp4'
    }));
}

async function main() {
    const isDryRun = process.argv.includes('--dry-run');
    const singleEpArg = process.argv.find(arg => arg.startsWith('--ep='));
    const singleEp = singleEpArg ? parseInt(singleEpArg.split('=')[1]) : null;

    console.log('='.repeat(70));
    console.log(`🎬 DRAMA CONVERSION SCRIPT: Levelku 9999, Tetua Baru 100`);
    console.log(`   Mode: ${isDryRun ? '🟡 DRY RUN' : '🔴 REAL RUN'}`);
    if (singleEp) console.log(`   Target Episode: ${singleEp}`);
    console.log('='.repeat(70));

    // Fetch episodes from DB
    const episodes = await prisma.episode.findMany({
        where: { dramaId: DRAMA_ID },
        orderBy: { episodeNumber: 'asc' }
    });

    console.log(`Found ${episodes.length} episodes in database.`);

    for (const ep of episodes) {
        if (singleEp && ep.episodeNumber !== singleEp) continue;

        // Skip if already has 540p and it's already mp4 for main URL, unless we target a single episode
        if (!singleEp && ep.videoUrl540p && ep.videoUrl.endsWith('.mp4')) {
            console.log(`⏭  Episode ${ep.episodeNumber} already converted. Skipping.`);
            continue;
        }

        console.log(`\n--- Processing Episode ${ep.episodeNumber} (ID: ${ep.id}) ---`);
        const sourceUrl = ep.videoUrl;
        console.log(`Source URL: ${sourceUrl}`);

        // We expect HLS playlist format like:
        // https://stream.shortlovers.id/melolo/levelku-9999-tetua-baru-100/episodes/002/playlist.m3u8
        const match = sourceUrl.match(/episodes\/(\d+)\/playlist\.m3u8/);
        if (!match) {
            console.warn(`⚠️ Warning: Source URL does not match expected HLS playlist path structure. Skipping.`);
            continue;
        }

        const epFolder = match[1];
        const local540 = `temp_ep${ep.episodeNumber}_540p.mp4`;
        const local720 = `temp_ep${ep.episodeNumber}_720p.mp4`;

        const r2Key540 = `melolo/${SLUG}/episodes/${epFolder}/540p.mp4`;
        const r2Key720 = `melolo/${SLUG}/episodes/${epFolder}/720p.mp4`;

        const dbUrl540 = `${R2_PUBLIC_URL}/${r2Key540}`;
        const dbUrl720 = `${R2_PUBLIC_URL}/${r2Key720}`;

        if (isDryRun) {
            console.log(`[DRY RUN] Would run FFmpeg:`);
            console.log(`  - 540p: ffmpeg -y -i "${sourceUrl}" -vf scale=-2:540 -c:v libx264 -preset fast -crf 28 -c:a aac -b:a 128k -movflags +faststart "${local540}"`);
            console.log(`  - 720p: ffmpeg -y -i "${sourceUrl}" -c:v libx264 -preset fast -crf 26 -c:a aac -b:a 128k -movflags +faststart "${local720}"`);
            console.log(`[DRY RUN] Would upload to R2 keys:`);
            console.log(`  - 540p Key: ${r2Key540}`);
            console.log(`  - 720p Key: ${r2Key720}`);
            console.log(`[DRY RUN] Would update Database fields:`);
            console.log(`  - videoUrl: ${dbUrl720}`);
            console.log(`  - videoUrl540p: ${dbUrl540}`);
            continue;
        }

        try {
            // 1. Transcode 720p MP4
            console.log(`🎥 [FFMPEG] Transcoding 720p HLS -> 720p MP4 (faststart)...`);
            const cmd720 = `ffmpeg -y -i "${sourceUrl}" -c:v libx264 -preset fast -crf 26 -c:a aac -b:a 128k -movflags +faststart "${local720}"`;
            execSync(cmd720, { stdio: 'inherit' });

            // 2. Transcode 540p MP4
            console.log(`🎥 [FFMPEG] Transcoding 720p HLS -> 540p MP4 (faststart)...`);
            const cmd540 = `ffmpeg -y -i "${sourceUrl}" -vf scale=-2:540 -c:v libx264 -preset fast -crf 28 -c:a aac -b:a 128k -movflags +faststart "${local540}"`;
            execSync(cmd540, { stdio: 'inherit' });

            // 3. Upload both to R2
            console.log(`📤 [UPLOAD] Uploading 720p MP4 to R2...`);
            await uploadToR2(local720, r2Key720);

            console.log(`📤 [UPLOAD] Uploading 540p MP4 to R2...`);
            await uploadToR2(local540, r2Key540);

            // 4. Update Database
            console.log(`💾 [DATABASE] Updating database fields...`);
            await prisma.episode.update({
                where: { id: ep.id },
                data: {
                    videoUrl: dbUrl720,
                    videoUrl540p: dbUrl540
                }
            });

            console.log(`✅ Episode ${ep.episodeNumber} successfully processed and registered!`);
        } catch (err) {
            console.error(`❌ Failed to process episode ${ep.episodeNumber}:`, err.message);
        } finally {
            // Clean up files
            if (fs.existsSync(local540)) fs.unlinkSync(local540);
            if (fs.existsSync(local720)) fs.unlinkSync(local720);
        }
    }

    await prisma.$disconnect();
    console.log('\n🏁 Process complete!');
}

main().catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
});
