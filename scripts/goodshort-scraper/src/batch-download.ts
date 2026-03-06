/**
 * Batch Download Script for GoodShort
 * Downloads all episodes from captured-episodes.json
 * 
 * Usage: npx ts-node src/batch-download.ts [dramatodownload]
 */

import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';

const VIDEO_CDN = 'https://v2-akm.goodreels.com';

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
        if (error.response?.status === 404) {
            return false;
        }
        return false;
    }
}

/**
 * Download all segments for an episode
 */
async function downloadEpisode(
    bookId: string,
    episode: Episode,
    outputDir: string
): Promise<string | null> {
    const { chapterId, token, videoId, resolution } = episode;
    const xxx = bookId.slice(-3);

    const segmentDir = path.join(outputDir, bookId, `chapter_${chapterId}`);
    if (!fs.existsSync(segmentDir)) {
        fs.mkdirSync(segmentDir, { recursive: true });
    }

    const downloadedFiles: string[] = [];
    let segmentNum = 0;
    let consecutiveFailures = 0;

    console.log(`    Downloading chapter ${chapterId}...`);

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
        console.log(' No segments found');
        return null;
    }

    console.log(` ${downloadedFiles.length} segments`);

    // Create segment list file
    const listFile = path.join(segmentDir, 'segments.txt');
    const fileList = downloadedFiles.map(f => `file '${path.basename(f)}'`).join('\n');
    fs.writeFileSync(listFile, fileList);

    // Combine with ffmpeg
    const outputFile = path.join(outputDir, bookId, `episode_${chapterId}.mp4`);

    try {
        execSync(
            `ffmpeg -y -f concat -safe 0 -i "${listFile}" -c copy "${outputFile}"`,
            { cwd: segmentDir, stdio: 'pipe' }
        );
        console.log(`    ✓ Created episode_${chapterId}.mp4`);
        return outputFile;
    } catch (error) {
        console.log(`    ⚠ ffmpeg failed, segments saved in ${segmentDir}`);
        return null;
    }
}

/**
 * Download all episodes for a drama
 */
async function downloadDrama(drama: Drama, outputDir: string): Promise<void> {
    console.log(`\n${'='.repeat(50)}`);
    console.log(`Drama: ${drama.bookId} (${drama.title})`);
    console.log(`Episodes: ${Object.keys(drama.episodes).length}`);
    console.log(`${'='.repeat(50)}`);

    const dramaDir = path.join(outputDir, drama.bookId);
    if (!fs.existsSync(dramaDir)) {
        fs.mkdirSync(dramaDir, { recursive: true });
    }

    // Download cover if available
    if (drama.cover) {
        const coverPath = path.join(dramaDir, 'cover.jpg');
        if (!fs.existsSync(coverPath)) {
            try {
                const coverResponse = await axios.get(drama.cover, { responseType: 'arraybuffer' });
                fs.writeFileSync(coverPath, Buffer.from(coverResponse.data));
                console.log(`  ✓ Downloaded cover`);
            } catch (e) {
                console.log(`  ⚠ Failed to download cover`);
            }
        }
    }

    // Sort episodes by chapterId
    const sortedEpisodes = Object.entries(drama.episodes)
        .sort((a, b) => parseInt(a[0]) - parseInt(b[0]));

    let successCount = 0;

    for (const [chapterId, episode] of sortedEpisodes) {
        const result = await downloadEpisode(drama.bookId, episode, outputDir);
        if (result) successCount++;
    }

    console.log(`\n  Summary: ${successCount}/${sortedEpisodes.length} episodes downloaded`);
}

/**
 * Main function
 */
async function main() {
    const args = process.argv.slice(2);
    const capturedFile = args[0] || 'captured-episodes.json';
    const specificDrama = args[1];

    if (!fs.existsSync(capturedFile)) {
        console.log(`
GoodShort Batch Downloader

Usage: 
  npx ts-node src/batch-download.ts [captured-file] [book-id]

Steps:
  1. Run Frida capture script: 
     frida -U -p [PID] -l frida/capture-episodes.js
  
  2. Browse dramas and open episodes in the app
  
  3. In Frida console, type 'save()' and copy the JSON
  
  4. Save JSON to captured-episodes.json
  
  5. Run this script:
     npx ts-node src/batch-download.ts

Example captured-episodes.json:
${JSON.stringify({
            dramas: {
                "31001250379": {
                    bookId: "31001250379",
                    title: "Drama Title",
                    cover: "https://...",
                    episodes: {
                        "634143": {
                            chapterId: "634143",
                            token: "qvytkzu2fs",
                            videoId: "vyzjkvvkc0",
                            resolution: "720p"
                        }
                    }
                }
            },
            lastUpdate: "2026-01-31T..."
        }, null, 2)}
    `);
        process.exit(1);
    }

    const capturedData: CapturedData = JSON.parse(fs.readFileSync(capturedFile, 'utf-8'));

    console.log('\n' + '='.repeat(60));
    console.log('GoodShort Batch Downloader');
    console.log('='.repeat(60));
    console.log(`Loaded: ${capturedFile}`);
    console.log(`Last update: ${capturedData.lastUpdate}`);
    console.log(`Dramas found: ${Object.keys(capturedData.dramas).length}`);

    const outputDir = './downloads';

    if (specificDrama) {
        // Download specific drama
        const drama = capturedData.dramas[specificDrama];
        if (!drama) {
            console.error(`Drama ${specificDrama} not found in captured data`);
            process.exit(1);
        }
        await downloadDrama(drama, outputDir);
    } else {
        // Download all dramas
        for (const [bookId, drama] of Object.entries(capturedData.dramas)) {
            await downloadDrama(drama, outputDir);
        }
    }

    console.log('\n' + '='.repeat(60));
    console.log('Download complete!');
    console.log('='.repeat(60) + '\n');
}

main().catch(console.error);
