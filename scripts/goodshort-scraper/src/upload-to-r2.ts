/**
 * Upload Downloaded Videos to Cloudflare R2
 * 
 * Scans downloads/ folder and uploads all MP4s and covers to R2
 * Generates metadata JSON with public R2 URLs
 * 
 * Usage: npx ts-node src/upload-to-r2.ts
 */

import { S3Client, PutObjectCommand, HeadObjectCommand } from '@aws-sdk/client-s3';
import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';

dotenv.config();

// R2 Configuration
const R2_CONFIG = {
    accountId: process.env.R2_ACCOUNT_ID!,
    accessKeyId: process.env.R2_ACCESS_KEY_ID!,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!,
    bucketName: process.env.R2_BUCKET_NAME || 'kingshortid',
    publicUrl: process.env.R2_PUBLIC_URL!,
};

// Initialize S3 client for R2
const r2Client = new S3Client({
    region: 'auto',
    endpoint: `https://${R2_CONFIG.accountId}.r2.cloudflarestorage.com`,
    credentials: {
        accessKeyId: R2_CONFIG.accessKeyId,
        secretAccessKey: R2_CONFIG.secretAccessKey,
    },
});

interface UploadResult {
    bookId: string;
    coverUrl: string | null;
    episodes: {
        chapterId: string;
        videoUrl: string;
        fileSize: number;
    }[];
}

/**
 * Check if file already exists in R2
 */
async function fileExistsInR2(key: string): Promise<boolean> {
    try {
        await r2Client.send(new HeadObjectCommand({
            Bucket: R2_CONFIG.bucketName,
            Key: key,
        }));
        return true;
    } catch (error: any) {
        if (error.name === 'NotFound') {
            return false;
        }
        throw error;
    }
}

/**
 * Upload file to R2
 */
async function uploadToR2(
    filePath: string,
    key: string,
    contentType: string
): Promise<string> {
    const fileBuffer = fs.readFileSync(filePath);

    // Check if already uploaded (skip to save time)
    const exists = await fileExistsInR2(key);
    if (exists) {
        console.log(`    ⏭️  Already uploaded: ${key}`);
        return `${R2_CONFIG.publicUrl}/${key}`;
    }

    await r2Client.send(new PutObjectCommand({
        Bucket: R2_CONFIG.bucketName,
        Key: key,
        Body: fileBuffer,
        ContentType: contentType,
    }));

    const publicUrl = `${R2_CONFIG.publicUrl}/${key}`;
    console.log(`    ✅ Uploaded: ${key}`);
    return publicUrl;
}

/**
 * Process a single drama folder
 */
async function processDrama(dramaPath: string): Promise<UploadResult> {
    const bookId = path.basename(dramaPath);

    console.log(`\n${'='.repeat(50)}`);
    console.log(`Processing Drama: ${bookId}`);
    console.log(`${'='.repeat(50)}`);

    const result: UploadResult = {
        bookId,
        coverUrl: null,
        episodes: [],
    };

    // Upload cover if exists
    const coverPath = path.join(dramaPath, 'cover.jpg');
    if (fs.existsSync(coverPath)) {
        const coverKey = `goodshort-content/${bookId}/cover.jpg`;
        result.coverUrl = await uploadToR2(coverPath, coverKey, 'image/jpeg');
    }

    // Upload all episode MP4s
    const episodeFiles = fs.readdirSync(dramaPath)
        .filter(file => file.startsWith('episode_') && file.endsWith('.mp4'))
        .sort();

    console.log(`  Found ${episodeFiles.length} episodes to upload`);

    for (const episodeFile of episodeFiles) {
        const episodePath = path.join(dramaPath, episodeFile);
        const chapterId = episodeFile.match(/episode_(\d+)\.mp4/)?.[1];

        if (!chapterId) {
            console.log(`  ⚠️  Skipping invalid filename: ${episodeFile}`);
            continue;
        }

        const videoKey = `goodshort-content/${bookId}/${chapterId}.mp4`;
        const videoUrl = await uploadToR2(episodePath, videoKey, 'video/mp4');

        const fileSize = fs.statSync(episodePath).size;

        result.episodes.push({
            chapterId,
            videoUrl,
            fileSize,
        });
    }

    console.log(`  ✓ Uploaded ${result.episodes.length} episodes + cover`);

    return result;
}

/**
 * Main upload function
 */
async function main() {
    console.log('\n' + '='.repeat(60));
    console.log('GoodShort R2 Upload Tool');
    console.log('='.repeat(60));

    // Validate environment
    if (!R2_CONFIG.accountId || !R2_CONFIG.accessKeyId || !R2_CONFIG.secretAccessKey || !R2_CONFIG.publicUrl) {
        console.error('\n❌ Missing R2 configuration in .env:');
        console.error('   R2_ACCOUNT_ID');
        console.error('   R2_ACCESS_KEY_ID');
        console.error('   R2_SECRET_ACCESS_KEY');
        console.error('   R2_PUBLIC_URL');
        process.exit(1);
    }

    const downloadsDir = path.join(__dirname, '..', 'downloads');

    if (!fs.existsSync(downloadsDir)) {
        console.error('\n❌ downloads/ folder not found');
        console.error('   Run batch-download.ts first to download videos');
        process.exit(1);
    }

    // Find all drama folders
    const dramaFolders = fs.readdirSync(downloadsDir)
        .map(name => path.join(downloadsDir, name))
        .filter(p => fs.statSync(p).isDirectory());

    console.log(`\nFound ${dramaFolders.length} drama folders to process\n`);

    const results: UploadResult[] = [];

    for (const dramaPath of dramaFolders) {
        try {
            const result = await processDrama(dramaPath);
            results.push(result);
        } catch (error: any) {
            console.error(`\n❌ Failed to upload drama ${path.basename(dramaPath)}:`, error.message);
        }
    }

    // Save upload results to JSON
    const outputFile = path.join(__dirname, '..', 'r2-upload-results.json');
    fs.writeFileSync(outputFile, JSON.stringify({
        uploadedAt: new Date().toISOString(),
        totalDramas: results.length,
        totalEpisodes: results.reduce((sum, r) => sum + r.episodes.length, 0),
        dramas: results,
    }, null, 2));

    console.log('\n' + '='.repeat(60));
    console.log('✅ Upload Complete!');
    console.log('='.repeat(60));
    console.log(`Total Dramas: ${results.length}`);
    console.log(`Total Episodes: ${results.reduce((sum, r) => sum + r.episodes.length, 0)}`);
    console.log(`\n📄 Results saved to: ${outputFile}`);
    console.log('\nNext step: Run import-to-kingshortid.ts to add to database');
    console.log('='.repeat(60) + '\n');
}

main().catch(console.error);
