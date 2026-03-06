/**
 * GoodShort Video Downloader
 * Downloads HLS video segments and combines them into MP4
 * 
 * Usage: npx ts-node src/download-video.ts <bookId> <chapterId> <token> <videoId> <segmentCount>
 */

import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';

const VIDEO_CDN = 'https://v2-akm.goodreels.com';

interface DownloadOptions {
    bookId: string;
    chapterId: string;
    token: string;
    videoId: string;
    startSegment?: number;
    endSegment?: number;
    resolution?: '720p' | '1080p' | '480p';
    outputDir?: string;
}

/**
 * Generate video segment URL
 */
function getSegmentUrl(opts: DownloadOptions, segmentNum: number): string {
    const { bookId, chapterId, token, videoId, resolution = '720p' } = opts;
    const xxx = bookId.slice(-3); // Last 3 digits
    const segment = segmentNum.toString().padStart(6, '0');

    return `${VIDEO_CDN}/mts/books/${xxx}/${bookId}/${chapterId}/${token}/${resolution}/${videoId}_${resolution}_${segment}.ts`;
}

/**
 * Download a single segment
 */
async function downloadSegment(url: string, outputPath: string): Promise<boolean> {
    try {
        const response = await axios.get(url, {
            responseType: 'arraybuffer',
            timeout: 30000,
            headers: {
                'Accept-Encoding': 'identity',
                'User-Agent': 'com.newreading.goodreels/2.7.8.2078 (Linux;Android 11) ExoPlayerLib/2.18.2'
            }
        });

        fs.writeFileSync(outputPath, Buffer.from(response.data));
        return true;
    } catch (error: any) {
        if (error.response?.status === 404) {
            return false; // Segment doesn't exist (end of video)
        }
        console.error(`Error downloading ${url}:`, error.message);
        return false;
    }
}

/**
 * Download all segments for a video
 */
async function downloadAllSegments(opts: DownloadOptions): Promise<string[]> {
    const { outputDir = './downloads', bookId, chapterId, startSegment = 0 } = opts;

    const segmentDir = path.join(outputDir, `${bookId}_${chapterId}`);
    if (!fs.existsSync(segmentDir)) {
        fs.mkdirSync(segmentDir, { recursive: true });
    }

    const downloadedFiles: string[] = [];
    let segmentNum = startSegment;
    let consecutiveFailures = 0;

    console.log(`\nDownloading segments for book ${bookId}, chapter ${chapterId}...`);

    while (consecutiveFailures < 3) {
        const url = getSegmentUrl(opts, segmentNum);
        const fileName = `segment_${segmentNum.toString().padStart(6, '0')}.ts`;
        const filePath = path.join(segmentDir, fileName);

        // Skip if already downloaded
        if (fs.existsSync(filePath) && fs.statSync(filePath).size > 0) {
            console.log(`  Segment ${segmentNum}: Already exists, skipping`);
            downloadedFiles.push(filePath);
            segmentNum++;
            consecutiveFailures = 0;
            continue;
        }

        const success = await downloadSegment(url, filePath);

        if (success) {
            const size = fs.statSync(filePath).size;
            console.log(`  Segment ${segmentNum}: Downloaded (${(size / 1024).toFixed(1)} KB)`);
            downloadedFiles.push(filePath);
            consecutiveFailures = 0;
        } else {
            console.log(`  Segment ${segmentNum}: Not found`);
            consecutiveFailures++;
        }

        segmentNum++;

        // Rate limiting - be gentle on the server
        await new Promise(resolve => setTimeout(resolve, 100));
    }

    console.log(`\nDownloaded ${downloadedFiles.length} segments`);
    return downloadedFiles;
}

/**
 * Combine segments into a single MP4 using ffmpeg
 */
function combineSegments(segmentFiles: string[], outputPath: string): boolean {
    if (segmentFiles.length === 0) {
        console.error('No segments to combine');
        return false;
    }

    const segmentDir = path.dirname(segmentFiles[0]);
    const listFile = path.join(segmentDir, 'segments.txt');

    // Create file list for ffmpeg
    const fileList = segmentFiles.map(f => `file '${path.basename(f)}'`).join('\n');
    fs.writeFileSync(listFile, fileList);

    try {
        console.log(`\nCombining ${segmentFiles.length} segments into ${outputPath}...`);

        // Use ffmpeg to concatenate and convert to MP4
        execSync(
            `ffmpeg -y -f concat -safe 0 -i "${listFile}" -c copy "${outputPath}"`,
            { cwd: segmentDir, stdio: 'inherit' }
        );

        console.log(`✓ Created ${outputPath}`);
        return true;
    } catch (error: any) {
        console.error('Failed to combine segments:', error.message);
        console.log('Make sure ffmpeg is installed: choco install ffmpeg');
        return false;
    }
}

/**
 * Main download function
 */
async function downloadVideo(opts: DownloadOptions): Promise<string | null> {
    const segments = await downloadAllSegments(opts);

    if (segments.length === 0) {
        console.error('No segments downloaded');
        return null;
    }

    const outputDir = opts.outputDir || './downloads';
    const outputFile = path.join(outputDir, `${opts.bookId}_${opts.chapterId}.mp4`);

    const success = combineSegments(segments, outputFile);

    return success ? outputFile : null;
}

// CLI usage
async function main() {
    const args = process.argv.slice(2);

    if (args.length < 4) {
        console.log(`
GoodShort Video Downloader

Usage: npx ts-node src/download-video.ts <bookId> <chapterId> <token> <videoId> [startSegment]

Example (from captured data):
  npx ts-node src/download-video.ts 31001250379 634143 qvytkzu2fs vyzjkvvkc0

The script will:
1. Download all HLS segments (.ts files)
2. Combine them into a single MP4 (requires ffmpeg)
    `);
        process.exit(1);
    }

    const [bookId, chapterId, token, videoId, startSegmentStr] = args;

    const result = await downloadVideo({
        bookId,
        chapterId,
        token,
        videoId,
        startSegment: startSegmentStr ? parseInt(startSegmentStr) : 0,
        outputDir: './downloads'
    });

    if (result) {
        console.log(`\n✅ Video saved to: ${result}`);
    } else {
        console.error('\n❌ Download failed');
        process.exit(1);
    }
}

main().catch(console.error);

export { downloadVideo, downloadAllSegments, getSegmentUrl };
