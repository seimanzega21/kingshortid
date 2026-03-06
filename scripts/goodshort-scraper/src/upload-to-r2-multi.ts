/**
 * R2 Upload Script - Multi Resolution Support
 * Uploads both 540p and 720p videos to R2
 * 
 * Usage: npx ts-node src/upload-to-r2-multi.ts
 */

import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';

dotenv.config();

const RESOLUTIONS = ['540p', '720p'];

interface UploadResult {
    uploadedAt: string;
    totalDramas: number;
    totalEpisodes: number;
    dramas: {
        bookId: string;
        coverUrl: string | null;
        episodes: {
            chapterId: string;
            videoUrl720p: string;
            videoUrl540p: string | null;
            fileSize720p: number;
            fileSize540p: number | null;
        }[];
    }[];
}

// Initialize R2 client
const r2Client = new S3Client({
    region: 'auto',
    endpoint: `https://${process.env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com`,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID!,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!,
    },
});

/**
 * Upload a file to R2
 */
async function uploadToR2(
    filePath: string,
    key: string
): Promise<string> {
    const fileContent = fs.readFileSync(filePath);

    await r2Client.send(
        new PutObjectCommand({
            Bucket: process.env.R2_BUCKET_NAME!,
            Key: key,
            Body: fileContent,
            ContentType: key.endsWith('.mp4') ? 'video/mp4' : 'image/jpeg',
        })
    );

    return `${process.env.R2_PUBLIC_URL}/${key}`;
}

/**
 * Process a single drama folder
 */
async function processDrama(dramaFolder: string, downloadsDir: string): Promise<any> {
    const bookId = path.basename(dramaFolder);

    console.log(`\n${'='.repeat(60)}`);
    console.log(`Processing Drama: ${bookId}`);
    console.log(`${'='.repeat(60)}`);

    const result: any = {
        bookId,
        coverUrl: null,
        episodes: [],
    };

    // Upload cover
    const coverPath = path.join(dramaFolder, 'cover.jpg');
    if (fs.existsSync(coverPath)) {
        try {
            const coverKey = `goodshort-content/${bookId}/cover.jpg`;
            result.coverUrl = await uploadToR2(coverPath, coverKey);
            console.log(`✓ Cover uploaded`);
        } catch (error: any) {
            console.log(`⚠ Cover upload failed: ${error.message}`);
        }
    }

    // Find all episodes (look for _720p.mp4 files)
    const files = fs.readdirSync(dramaFolder);
    const episodeFiles = files.filter(f => f.match(/episode_(\d+)_720p\.mp4$/));

    console.log(`Found ${episodeFiles.length} episodes to upload`);

    for (const file of episodeFiles) {
        const match = file.match(/episode_(\d+)_720p\.mp4$/);
        if (!match) continue;

        const chapterId = match[1];
        const file720p = path.join(dramaFolder, file);
        const file540p = path.join(dramaFolder, `episode_${chapterId}_540p.mp4`);

        console.log(`\n  Episode ${chapterId}:`);

        const episodeData: any = {
            chapterId,
            videoUrl720p: '',
            videoUrl540p: null,
            fileSize720p: 0,
            fileSize540p: null,
        };

        // Upload 720p (required)
        if (fs.existsSync(file720p)) {
            try {
                const key = `goodshort-content/${bookId}/${chapterId}_720p.mp4`;
                episodeData.videoUrl720p = await uploadToR2(file720p, key);
                episodeData.fileSize720p = fs.statSync(file720p).size;

                const sizeMB = (episodeData.fileSize720p / (1024 * 1024)).toFixed(2);
                console.log(`    720p: ✓ ${sizeMB}MB`);
            } catch (error: any) {
                console.log(`    720p: ✗ ${error.message}`);
                continue; // Skip episode if 720p fails
            }
        } else {
            console.log(`    720p: ✗ File not found`);
            continue;
        }

        // Upload 540p (optional)
        if (fs.existsSync(file540p)) {
            try {
                const key = `goodshort-content/${bookId}/${chapterId}_540p.mp4`;
                episodeData.videoUrl540p = await uploadToR2(file540p, key);
                episodeData.fileSize540p = fs.statSync(file540p).size;

                const sizeMB = (episodeData.fileSize540p / (1024 * 1024)).toFixed(2);
                console.log(`    540p: ✓ ${sizeMB}MB`);
            } catch (error: any) {
                console.log(`    540p: ✗ ${error.message}`);
            }
        } else {
            console.log(`    540p: ⏭ Not available`);
        }

        result.episodes.push(episodeData);
    }

    console.log(`\n✓ Uploaded ${result.episodes.length} episodes for drama ${bookId}`);

    return result;
}

/**
 * Main function
 */
async function main() {
    console.log('\n' + '='.repeat(60));
    console.log('GoodShort R2 Upload - Multi Resolution (540p + 720p)');
    console.log('='.repeat(60) + '\n');

    // Validate environment
    const requiredEnv = [
        'R2_ACCOUNT_ID',
        'R2_ACCESS_KEY_ID',
        'R2_SECRET_ACCESS_KEY',
        'R2_BUCKET_NAME',
        'R2_PUBLIC_URL',
    ];

    for (const key of requiredEnv) {
        if (!process.env[key]) {
            console.error(`❌ Missing environment variable: ${key}`);
            console.error('   Check .env file');
            process.exit(1);
        }
    }

    const downloadsDir = path.join(__dirname, '..', 'downloads');
    if (!fs.existsSync(downloadsDir)) {
        console.error('❌ downloads/ directory not found');
        console.error('   Run npm run download first');
        process.exit(1);
    }

    // Find all drama folders
    const folders = fs.readdirSync(downloadsDir, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory())
        .map(dirent => path.join(downloadsDir, dirent.name));

    if (folders.length === 0) {
        console.log('❌ No drama folders found in downloads/');
        process.exit(1);
    }

    console.log(`Found ${folders.length} drama folder(s) to process\n`);

    const uploadResult: UploadResult = {
        uploadedAt: new Date().toISOString(),
        totalDramas: 0,
        totalEpisodes: 0,
        dramas: [],
    };

    // Process each drama
    for (const folder of folders) {
        try {
            const result = await processDrama(folder, downloadsDir);

            if (result.episodes.length > 0) {
                uploadResult.dramas.push(result);
                uploadResult.totalEpisodes += result.episodes.length;
            }
        } catch (error: any) {
            console.error(`\n❌ Failed to process ${path.basename(folder)}: ${error.message}`);
        }
    }

    uploadResult.totalDramas = uploadResult.dramas.length;

    // Save upload results
    const resultPath = path.join(__dirname, '..', 'r2-upload-results.json');
    fs.writeFileSync(resultPath, JSON.stringify(uploadResult, null, 2));

    console.log('\n' + '='.repeat(60));
    console.log('✅ Upload Complete!');
    console.log('='.repeat(60));
    console.log(`Dramas: ${uploadResult.totalDramas}`);
    console.log(`Episodes: ${uploadResult.totalEpisodes}`);
    console.log(`Results saved to: r2-upload-results.json`);
    console.log('='.repeat(60) + '\n');
    console.log('Next step:');
    console.log('  npx ts-node src/import-goodshort.ts');
    console.log('');
}

main().catch(error => {
    console.error('\n❌ Upload failed:', error.message);
    process.exit(1);
});
