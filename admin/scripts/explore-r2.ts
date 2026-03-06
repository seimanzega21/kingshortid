import { ListObjectsV2Command, GetObjectCommand } from '@aws-sdk/client-s3';
import { r2Client, R2_BUCKET } from '../config/r2';

interface BucketAnalysis {
    totalObjects: number;
    totalSize: number;
    folders: Map<string, number>;
    fileTypes: Map<string, number>;
    sampleFiles: string[];
    structure: string[];
}

async function exploreR2Bucket() {
    console.log('🔍 Exploring R2 Bucket: ' + R2_BUCKET);
    console.log('='.repeat(60));

    const analysis: BucketAnalysis = {
        totalObjects: 0,
        totalSize: 0,
        folders: new Map(),
        fileTypes: new Map(),
        sampleFiles: [],
        structure: [],
    };

    try {
        let continuationToken: string | undefined;
        let pageCount = 0;

        // List all objects (with pagination)
        do {
            pageCount++;
            console.log(`\n📄 Fetching page ${pageCount}...`);

            const command = new ListObjectsV2Command({
                Bucket: R2_BUCKET,
                MaxKeys: 1000,
                ContinuationToken: continuationToken,
            });

            const response = await r2Client.send(command);

            if (!response.Contents || response.Contents.length === 0) {
                console.log('❌ Bucket kosong atau tidak ada akses');
                break;
            }

            // Process each object
            for (const item of response.Contents) {
                if (!item.Key) continue;

                analysis.totalObjects++;
                analysis.totalSize += item.Size || 0;

                // Extract folder structure
                const parts = item.Key.split('/');
                if (parts.length > 1) {
                    const folder = parts[0];
                    analysis.folders.set(folder, (analysis.folders.get(folder) || 0) + 1);
                }

                // Extract file type
                const ext = item.Key.split('.').pop()?.toLowerCase() || 'no-ext';
                analysis.fileTypes.set(ext, (analysis.fileTypes.get(ext) || 0) + 1);

                // Collect sample files
                if (analysis.sampleFiles.length < 20) {
                    analysis.sampleFiles.push(item.Key);
                }

                // Collect structure samples
                if (analysis.structure.length < 50) {
                    analysis.structure.push(`${item.Key} (${formatBytes(item.Size || 0)})`);
                }
            }

            continuationToken = response.NextContinuationToken;

            console.log(`✅ Processed ${response.Contents.length} objects`);

        } while (continuationToken);

        // Print analysis
        printAnalysis(analysis);

    } catch (error: any) {
        console.error('\n❌ Error exploring bucket:');
        console.error(error.message);
        if (error.$metadata) {
            console.error('Status Code:', error.$metadata.httpStatusCode);
        }
    }
}

function printAnalysis(analysis: BucketAnalysis) {
    console.log('\n');
    console.log('='.repeat(60));
    console.log('📊 BUCKET ANALYSIS REPORT');
    console.log('='.repeat(60));

    console.log(`\n📦 Total Objects: ${analysis.totalObjects.toLocaleString()}`);
    console.log(`💾 Total Size: ${formatBytes(analysis.totalSize)}`);

    console.log('\n📁 Top-Level Folders:');
    const sortedFolders = Array.from(analysis.folders.entries())
        .sort((a, b) => b[1] - a[1]);

    sortedFolders.forEach(([folder, count]) => {
        console.log(`   - ${folder}: ${count} files`);
    });

    console.log('\n📄 File Types Distribution:');
    const sortedTypes = Array.from(analysis.fileTypes.entries())
        .sort((a, b) => b[1] - a[1]);

    sortedTypes.forEach(([type, count]) => {
        console.log(`   - .${type}: ${count} files`);
    });

    console.log('\n🗂️ Sample Structure (first 50 files):');
    analysis.structure.forEach(file => {
        console.log(`   ${file}`);
    });

    console.log('\n');
    console.log('='.repeat(60));
    console.log('✅ EXPLORATION COMPLETE');
    console.log('='.repeat(60));
}

function formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Run exploration
exploreR2Bucket()
    .then(() => {
        console.log('\n💡 Next Steps:');
        console.log('1. Review the structure above');
        console.log('2. Update import script based on actual folder structure');
        console.log('3. Run import script to populate database');
        process.exit(0);
    })
    .catch((error) => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
