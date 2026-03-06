/**
 * Batch Download Script - Multi Resolution Support
 * Downloads 540p and 720p for each episode
 * 
 * Usage: npm run download
 */

import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';

const VIDEO_CDN = 'https://v2-akm.goodreels.com';
const RESOLUTIONS = ['540p', '720p']; // Download both resolutions

interface Episode {
    chapterId: string;
    token: string;
    videoId: string;
    resolution: string;
}

interface Drama {
    bookId: string;
    title: string;
    cover: string | null;
    episodes: { [chapterId: string]: Episode };
    metadata?: any;
}

interface CapturedData {
    dramas: { [bookId: string]: Drama };
    lastUpdate: string;
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
        return false;
    }
}

/**
 * Download episode at specific resolution
 */
async function downloadEpisodeResolution(
    bookId: string,
    episode: Episode,
    resolution: string,
    outputDir: string
): Promise<string | null> {
    const { chapterId, token, videoId } = episode;
    const xxx = bookId.slice(-3);

    const segmentDir = path.join(outputDir, bookId, `chapter_${chapterId}_${resolution}`);
    if (!fs.existsSync(segmentDir)) {
        fs.mkdirSync(segmentDir, { recursive: true });
    }

    const downloadedFiles: string[] = [];
    let segmentNum = 0;
    let consecutiveFailures = 0;

    while (consecutiveFailures < 3) {
        const segment = segmentNum.toString().padStart(6, '0');
        const url = `${VIDEO_CDN}/mts/books/${xxx}/${bookId}/${chapterId}/${token}/${resolution}/${videoId}_${resolution}_${segment}.ts`;
        const fileName = `segment_${segment}.ts`;
        const filePath = path.join(segmentDir, fileName);

        // Skip if already downloaded
        if (fs.existsSync(filePath) && fs.statSync(filePath).size > 0) {
            downloadedFiles.push(filePath);
            segmentNum++;
            consecutiveFailures = 0;
            continue;
        }

        const success = await downloadSegment(url, filePath);

        if (success) {
            downloadedFiles.push(filePath);
            consecutiveFailures = 0;
            process.stdout.write('.');
        } else {
            consecutiveFailures++;
        }

        segmentNum++;
        await new Promise(resolve => setTimeout(resolve, 50));
    }

    if (downloadedFiles.length === 0) {
        return null;
    }

    // Create segment list file
    const listFile = path.join(segmentDir, 'segments.txt');
    const fileList = downloadedFiles.map(f => `file '${path.basename(f)}'`).join('\n');
    fs.writeFileSync(listFile, fileList);

    // Combine with ffmpeg
    const outputFile = path.join(outputDir, bookId, `episode_${chapterId}_${resolution}.mp4`);

    try {
        execSync(
            `ffmpeg -y -f concat -safe 0 -i "${listFile}" -c copy "${outputFile}"`,
            { cwd: segmentDir, stdio: 'pipe' }
        );
        return outputFile;
    } catch (error) {
        console.log(`    ⚠ ffmpeg failed for ${resolution}`);
        return null;
    }
}

/**
 * Download episode in multiple resolutions
 */
async function downloadEpisode(
    bookId: string,
    episode: Episode,
    outputDir: string
): Promise<{ [resolution: string]: string | null }> {
    const { chapterId } = episode;
    const results: { [resolution: string]: string | null } = {};

    console.log(`    Episode ${chapterId}:`);

    for (const resolution of RESOLUTIONS) {
        process.stdout.write(`      ${resolution}: `);

        const outputFile = await downloadEpisodeResolution(
            bookId,
            episode,
            resolution,
            outputDir
        );

        results[resolution] = outputFile;

        if (outputFile) {
            const stats = fs.statSync(outputFile);
            const sizeMB = (stats.size / (1024 * 1024)).toFixed(2);
            console.log(` ✓ ${sizeMB}MB`);
        } else {
            console.log(` ✗ Failed`);
        }
    }

    return results;
}

/**
 * Download all episodes for a drama
 */
async function downloadDrama(drama: Drama, outputDir: string): Promise<void> {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`Drama: ${drama.title || drama.bookId}`);
    console.log(`Episodes: ${Object.keys(drama.episodes).length}`);
    console.log(`${'='.repeat(60)}`);

    const dramaDir = path.join(outputDir, drama.bookId);
    if (!fs.existsSync(dramaDir)) {
        fs.mkdirSync(dramaDir, { recursive: true });
    }

    // Download cover if available
    if (drama.cover) {
        const coverPath = path.join(dramaDir, 'cover.jpg');
        if (!fs.existsSync(coverPath)) {
            try {
                const response = await axios.get(drama.cover, { responseType: 'arraybuffer' });
                fs.writeFileSync(coverPath, Buffer.from(response.data));
                console.log(`  ✓ Cover downloaded`);
            } catch (error) {
                console.log(`  ⚠ Cover download failed`);
            }
        }
    }

    // Download all episodes
    let successCount = 0;
    const episodes = Object.values(drama.episodes);

    for (let i = 0; i < episodes.length; i++) {
        const episode = episodes[i];
        const results = await downloadEpisode(drama.bookId, episode, outputDir);

        // Count as success if at least one resolution downloaded
        if (Object.values(results).some(r => r !== null)) {
            successCount++;
        }

        // Small delay between episodes
        if (i < episodes.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 200));
        }
    }

    console.log(`\n✓ Downloaded ${successCount}/${episodes.length} episodes`);
}

/**
 * Main function
 */
async function main() {
    console.log('\n' + '='.repeat(60));
    console.log('GoodShort Batch Download - Dual Resolution (540p + 720p)');
    console.log('='.repeat(60) + '\n');

    const capturedFile = path.join(__dirname, '..', 'captured-episodes.json');
    if (!fs.existsSync(capturedFile)) {
        console.error('❌ captured-episodes.json not found');
        console.error('   Run Frida capture script first');
        process.exit(1);
    }

    const data: CapturedData = JSON.parse(fs.readFileSync(capturedFile, 'utf-8'));
    const dramas = Object.values(data.dramas);

    if (dramas.length === 0) {
        console.log('❌ No dramas found in captured data');
        process.exit(1);
    }

    console.log(`Found ${dramas.length} drama(s) to download\n`);

    const outputDir = path.join(__dirname, '..', 'downloads');
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    // Download all dramas
    for (const drama of dramas) {
        try {
            await downloadDrama(drama, outputDir);
        } catch (error: any) {
            console.error(`\n❌ Failed to download drama ${drama.bookId}:`, error.message);
        }
    }

    console.log('\n' + '='.repeat(60));
    console.log('✅ Batch download complete!');
    console.log(`Output: ${outputDir}`);
    console.log('='.repeat(60) + '\n');
    console.log('Next steps:');
    console.log('  1. npx ts-node src/upload-to-r2.ts');
    console.log('  2. npx ts-node src/import-goodshort.ts');
    console.log('');
}

main().catch(error => {
    console.error('\n❌ Script failed:', error.message);
    process.exit(1);
});
