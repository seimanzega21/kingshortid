import { GetObjectCommand, ListObjectsV2Command } from '@aws-sdk/client-s3';
import { r2Client, R2_BUCKET } from '../config/r2';
import fs from 'fs';
import path from 'path';

const DATA_DIR = path.join(__dirname, '../data');

// Ensure data directory exists
if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    console.log('📁 Created data directory:', DATA_DIR);
}

interface DownloadResult {
    key: string;
    outputPath: string;
    size: number;
    success: boolean;
    error?: string;
}

/**
 * Download a single file from R2
 */
async function downloadFile(key: string, outputPath: string): Promise<DownloadResult> {
    try {
        const command = new GetObjectCommand({
            Bucket: R2_BUCKET,
            Key: key,
        });

        const response = await r2Client.send(command);
        const data = await response.Body?.transformToString();

        if (!data) {
            return { key, outputPath, size: 0, success: false, error: 'Empty response' };
        }

        // Ensure directory exists
        const dir = path.dirname(outputPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }

        fs.writeFileSync(outputPath, data);

        return {
            key,
            outputPath,
            size: Buffer.byteLength(data, 'utf8'),
            success: true,
        };
    } catch (error: any) {
        return {
            key,
            outputPath,
            size: 0,
            success: false,
            error: error.message,
        };
    }
}

/**
 * List all JSON files in R2 bucket
 */
async function listJsonFiles(): Promise<string[]> {
    const jsonFiles: string[] = [];
    let continuationToken: string | undefined;

    do {
        const command = new ListObjectsV2Command({
            Bucket: R2_BUCKET,
            MaxKeys: 1000,
            ContinuationToken: continuationToken,
        });

        const response = await r2Client.send(command);

        if (response.Contents) {
            for (const item of response.Contents) {
                if (item.Key?.endsWith('.json')) {
                    jsonFiles.push(item.Key);
                }
            }
        }

        continuationToken = response.NextContinuationToken;
    } while (continuationToken);

    return jsonFiles;
}

/**
 * Download all JSON metadata files from R2
 */
async function downloadAllMetadata() {
    console.log('🔍 Scanning R2 for JSON metadata files...');

    const jsonFiles = await listJsonFiles();
    console.log(`📄 Found ${jsonFiles.length} JSON files`);

    if (jsonFiles.length === 0) {
        console.log('❌ No JSON files found in bucket');
        return;
    }

    console.log('\n📥 Downloading metadata files...\n');

    const results: DownloadResult[] = [];

    for (let i = 0; i < jsonFiles.length; i++) {
        const key = jsonFiles[i];
        const outputPath = path.join(DATA_DIR, key);

        console.log(`[${i + 1}/${jsonFiles.length}] Downloading: ${key}`);
        const result = await downloadFile(key, outputPath);
        results.push(result);

        if (result.success) {
            console.log(`   ✅ Saved to: ${outputPath} (${formatBytes(result.size)})`);
        } else {
            console.log(`   ❌ Failed: ${result.error}`);
        }
    }

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('📊 DOWNLOAD SUMMARY');
    console.log('='.repeat(60));

    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);

    console.log(`✅ Successful: ${successful.length}`);
    console.log(`❌ Failed: ${failed.length}`);
    console.log(`📦 Total Size: ${formatBytes(successful.reduce((sum, r) => sum + r.size, 0))}`);

    if (failed.length > 0) {
        console.log('\n⚠️ Failed Downloads:');
        failed.forEach(r => console.log(`   - ${r.key}: ${r.error}`));
    }

    console.log('\n📁 Files saved to:', DATA_DIR);
}

function formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Run
downloadAllMetadata()
    .then(() => {
        console.log('\n✅ Download complete!');
        console.log('💡 Next: Run import-from-r2.ts to import to database');
        process.exit(0);
    })
    .catch((error) => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
