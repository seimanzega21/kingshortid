/**
 * Upload HLS files to R2
 * Uploads: playlist.m3u8 + video.ts for each book/chapter
 */
import 'dotenv/config';
import { S3Client, PutObjectCommand, ListBucketsCommand } from '@aws-sdk/client-s3';
import * as fs from 'fs';
import * as path from 'path';

const r2Client = new S3Client({
    region: 'auto',
    endpoint: process.env.R2_ENDPOINT!,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID!,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!,
    },
});

const R2_BUCKET = process.env.R2_BUCKET_NAME || 'shortlovers';

interface UploadResult {
    localPath: string;
    r2Key: string;
    success: boolean;
    size: number;
}

async function uploadFile(localPath: string, r2Key: string, contentType: string): Promise<UploadResult> {
    const stats = fs.statSync(localPath);
    const content = fs.readFileSync(localPath);

    try {
        await r2Client.send(new PutObjectCommand({
            Bucket: R2_BUCKET,
            Key: r2Key,
            Body: content,
            ContentType: contentType,
        }));
        return { localPath, r2Key, success: true, size: stats.size };
    } catch (error: any) {
        console.error(`  ✗ Failed ${r2Key}: ${error.message}`);
        return { localPath, r2Key, success: false, size: 0 };
    }
}

async function main() {
    console.log('============================================================');
    console.log('UPLOAD HLS TO R2');
    console.log('============================================================\n');

    // Check connection
    try {
        await r2Client.send(new ListBucketsCommand({}));
        console.log('✓ R2 connected\n');
    } catch (error: any) {
        console.error('✗ R2 connection failed:', error.message);
        return;
    }

    // Find HLS directories
    const hlsDir = path.join(__dirname, '..', 'scraped_data', 'hls');

    if (!fs.existsSync(hlsDir)) {
        console.error('No HLS directory found!');
        return;
    }

    const results: UploadResult[] = [];
    let totalSize = 0;

    // Iterate book directories
    const bookDirs = fs.readdirSync(hlsDir)
        .filter(f => !f.endsWith('.json'))
        .map(f => path.join(hlsDir, f))
        .filter(p => fs.statSync(p).isDirectory());

    console.log(`Found ${bookDirs.length} books to upload\n`);

    for (const bookDir of bookDirs) {
        const bookId = path.basename(bookDir);
        console.log(`[Book ${bookId}]`);

        // Get chapter directories
        const chapterDirs = fs.readdirSync(bookDir)
            .map(f => path.join(bookDir, f))
            .filter(p => fs.statSync(p).isDirectory());

        for (const chapterDir of chapterDirs) {
            const chapterId = path.basename(chapterDir);
            console.log(`  Episode ${chapterId}:`);

            // Upload playlist.m3u8
            const m3u8Path = path.join(chapterDir, 'playlist.m3u8');
            if (fs.existsSync(m3u8Path)) {
                const r2Key = `goodshort/${bookId}/episodes/${chapterId}/playlist.m3u8`;
                const result = await uploadFile(m3u8Path, r2Key, 'application/vnd.apple.mpegurl');
                results.push(result);
                if (result.success) {
                    console.log(`    ✓ playlist.m3u8`);
                    totalSize += result.size;
                }
            }

            // Upload video.ts
            const videoPath = path.join(chapterDir, 'video.ts');
            if (fs.existsSync(videoPath)) {
                const r2Key = `goodshort/${bookId}/episodes/${chapterId}/video.ts`;
                const result = await uploadFile(videoPath, r2Key, 'video/MP2T');
                results.push(result);
                if (result.success) {
                    const sizeMB = (result.size / 1024 / 1024).toFixed(2);
                    console.log(`    ✓ video.ts (${sizeMB} MB)`);
                    totalSize += result.size;
                }
            }
        }
    }

    // Also upload metadata
    const metadataPath = path.join(__dirname, '..', 'scraped_data', 'books_metadata.json');
    if (fs.existsSync(metadataPath)) {
        console.log('\n[Metadata]');
        const r2Key = 'goodshort/metadata.json';
        const result = await uploadFile(metadataPath, r2Key, 'application/json');
        results.push(result);
        if (result.success) {
            console.log('  ✓ metadata.json');
        }
    }

    // Summary
    console.log('\n============================================================');
    console.log('UPLOAD COMPLETE');
    console.log('============================================================');

    const successful = results.filter(r => r.success);
    console.log(`\n✓ Successful: ${successful.length}`);
    console.log(`✗ Failed: ${results.length - successful.length}`);
    console.log(`\nTotal uploaded: ${(totalSize / 1024 / 1024).toFixed(2)} MB`);

    console.log('\nR2 Structure:');
    console.log('  goodshort/');
    console.log('  ├── metadata.json');
    for (const bookDir of bookDirs.slice(0, 2)) {
        const bookId = path.basename(bookDir);
        console.log(`  └── ${bookId}/`);
        console.log(`      └── episodes/`);
        console.log(`          └── {chapterId}/`);
        console.log(`              ├── playlist.m3u8`);
        console.log(`              └── video.ts`);
    }
    if (bookDirs.length > 2) {
        console.log(`  └── ... (${bookDirs.length - 2} more books)`);
    }

    console.log('\nHLS URLs:');
    for (const r of successful.filter(r => r.r2Key.endsWith('.m3u8')).slice(0, 3)) {
        console.log(`  https://pub-xxx.r2.dev/${r.r2Key}`);
    }
}

main().catch(console.error);
