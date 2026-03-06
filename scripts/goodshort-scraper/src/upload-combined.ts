/**
 * Upload combined videos to R2
 */
import 'dotenv/config';
import { S3Client, PutObjectCommand, ListBucketsCommand } from '@aws-sdk/client-s3';
import * as fs from 'fs';
import * as path from 'path';

// R2 Configuration
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
    file: string;
    key: string;
    size: number;
    success: boolean;
    error?: string;
}

async function uploadFile(localPath: string, r2Key: string): Promise<UploadResult> {
    const stats = fs.statSync(localPath);
    const fileContent = fs.readFileSync(localPath);

    console.log(`  Uploading: ${path.basename(localPath)} (${(stats.size / 1024 / 1024).toFixed(2)} MB)`);

    try {
        await r2Client.send(new PutObjectCommand({
            Bucket: R2_BUCKET,
            Key: r2Key,
            Body: fileContent,
            ContentType: 'video/MP2T',
        }));

        console.log(`  ✓ Uploaded to: ${r2Key}`);
        return { file: localPath, key: r2Key, size: stats.size, success: true };
    } catch (error: any) {
        console.error(`  ✗ Failed: ${error.message}`);
        return { file: localPath, key: r2Key, size: stats.size, success: false, error: error.message };
    }
}

async function main() {
    console.log('============================================================');
    console.log('STEP 3: UPLOAD TO R2');
    console.log('============================================================\n');

    // Check R2 connection
    console.log('Checking R2 connection...');
    try {
        const response = await r2Client.send(new ListBucketsCommand({}));
        console.log(`✓ Connected! Buckets: ${response.Buckets?.map(b => b.Name).join(', ')}\n`);
    } catch (error: any) {
        console.error(`✗ R2 connection failed: ${error.message}`);
        console.log('\nPlease ensure R2 credentials are set in .env:');
        console.log('  R2_ENDPOINT=...');
        console.log('  R2_ACCESS_KEY_ID=...');
        console.log('  R2_SECRET_ACCESS_KEY=...');
        console.log('  R2_BUCKET_NAME=...');
        return;
    }

    // Find combined videos
    const combinedDir = path.join(__dirname, '..', 'scraped_data', 'combined');

    if (!fs.existsSync(combinedDir)) {
        console.error('No combined directory found!');
        return;
    }

    const files = fs.readdirSync(combinedDir)
        .filter(f => f.endsWith('.ts'))
        .map(f => path.join(combinedDir, f));

    console.log(`Found ${files.length} videos to upload:\n`);

    const results: UploadResult[] = [];

    for (const file of files) {
        const filename = path.basename(file);
        const [bookId, chapterId] = filename.replace('.ts', '').split('_');

        // R2 key structure: goodshort/bookId/episodes/chapterId.ts
        const r2Key = `goodshort/${bookId}/episodes/${chapterId}.ts`;

        const result = await uploadFile(file, r2Key);
        results.push(result);
    }

    // Summary
    console.log('\n============================================================');
    console.log('UPLOAD COMPLETE');
    console.log('============================================================');

    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);

    console.log(`\n✓ Successful: ${successful.length}`);
    console.log(`✗ Failed: ${failed.length}`);

    const totalSize = successful.reduce((acc, r) => acc + r.size, 0);
    console.log(`\nTotal uploaded: ${(totalSize / 1024 / 1024).toFixed(2)} MB`);

    console.log('\nUploaded files:');
    for (const r of successful) {
        console.log(`  ${r.key}`);
    }

    if (failed.length > 0) {
        console.log('\nFailed files:');
        for (const r of failed) {
            console.log(`  ${r.file}: ${r.error}`);
        }
    }
}

main().catch(console.error);
