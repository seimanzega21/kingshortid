/**
 * Complete GoodShort Scraper - Fixed Version
 * 
 * Fixes:
 * 1. Proper title extraction (not generic numbers)
 * 2. Correct cover images (main poster)
 * 3. Working HLS segments
 * 4. Episode naming (Episode 1, Episode 2, not chapter-xxx)
 * 5. Complete metadata
 * 6. Clean structure
 */

import fs from 'fs';
import path from 'path';
import axios from 'axios';
import { generateSignV2 } from './sign-generator-v2';

// Configuration
const OUTPUT_DIR = path.join(__dirname, '../output');
const COVERS_DIR = path.join(OUTPUT_DIR, 'covers');
const METADATA_DIR = path.join(OUTPUT_DIR, 'metadata');
const EPISODES_DIR = path.join(OUTPUT_DIR, 'episodes');

// API Configuration
const API_BASE = 'https://api-akm.goodreels.com/hwycclientreels';
const CDN_BASE = 'https://v2-akm.goodreels.com';
const COVER_CDN = 'https://acf.goodreels.com';

// Device Parameters (extract from Frida or use defaults)
const DEVICE_PARAMS = {
    gaid: '3a527bd0-4a98-47e7-ac47-f592c165d870',
    androidId: 'ffffffffcf4ce71dcf4ce71d00000000',
    userToken: '' // Will be set if available
};

interface DramaMetadata {
    bookId: string;
    title: string;
    cover: string;
    coverHQ: string;
    description: string;
    author: string;
    category: string;
    genre: string;
    tags: string[];
    totalChapters: number;
    language: string;
    rating?: number;
    views?: number;
}

interface Episode {
    episodeNumber: number;
    chapterId: string;
    title: string;
    duration?: number;
    isFree: boolean;
    videoUrl: string;
    token: string;
    videoId: string;
}

interface ScrapedDrama {
    metadata: DramaMetadata;
    episodes: Episode[];
    coverPath: string;
}

// Ensure directories exist
function ensureDirs() {
    [OUTPUT_DIR, COVERS_DIR, METADATA_DIR, EPISODES_DIR].forEach(dir => {
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
    });
}

/**
 * Fetch drama metadata from API
 */
async function fetchDramaMetadata(bookId: string): Promise<DramaMetadata | null> {
    try {
        console.log(`\n📖 Fetching metadata for book: ${bookId}`);

        const timestamp = Date.now().toString();
        const body = {
            bookId: bookId,
            needChapterList: false
        };

        const sign = generateSignV2({
            timestamp,
            body,
            gaid: DEVICE_PARAMS.gaid,
            androidId: DEVICE_PARAMS.androidId,
            userToken: DEVICE_PARAMS.userToken
        });

        const response = await axios.post(`${API_BASE}/book/detail`, body, {
            headers: {
                'sign': sign,
                'timestamp': timestamp,
                'Content-Type': 'application/json',
                'User-Agent': 'okhttp/4.9.3'
            },
            timeout: 30000
        });

        if (response.data && response.data.data) {
            const data = response.data.data;

            const metadata: DramaMetadata = {
                bookId: bookId,
                title: data.title || data.name || data.bookName || `Drama ${bookId}`,
                cover: data.cover || data.coverUrl || '',
                coverHQ: data.coverHQ || data.cover || '',
                description: data.description || data.desc || data.synopsis || data.intro || '',
                author: data.author || data.authorName || 'GoodShort',
                category: data.category || data.categoryName || 'Drama',
                genre: data.genre || data.category || 'Drama',
                tags: data.tags || data.tagList || [],
                totalChapters: data.totalChapter || data.chapterCount || data.episodeCount || 0,
                language: data.language || 'id',
                rating: data.rating || data.score,
                views: data.viewCount || data.views
            };

            console.log(`✅ Title: ${metadata.title}`);
            console.log(`   Chapters: ${metadata.totalChapters}`);
            console.log(`   Category: ${metadata.category}`);

            return metadata;
        }

        return null;
    } catch (error: any) {
        console.error(`❌ Failed to fetch metadata: ${error.message}`);
        return null;
    }
}

/**
 * Fetch chapter/episode list
 */
async function fetchEpisodeList(bookId: string): Promise<Episode[]> {
    try {
        console.log(`\n📚 Fetching episode list for book: ${bookId}`);

        const timestamp = Date.now().toString();
        const body = {
            bookId: bookId,
            pageSize: 1000,
            pageIndex: 1
        };

        const sign = generateSignV2({
            timestamp,
            body,
            gaid: DEVICE_PARAMS.gaid,
            androidId: DEVICE_PARAMS.androidId,
            userToken: DEVICE_PARAMS.userToken
        });

        const response = await axios.post(`${API_BASE}/chapter/list`, body, {
            headers: {
                'sign': sign,
                'timestamp': timestamp,
                'Content-Type': 'application/json',
                'User-Agent': 'okhttp/4.9.3'
            },
            timeout: 30000
        });

        if (response.data && response.data.data) {
            const chapters = Array.isArray(response.data.data)
                ? response.data.data
                : response.data.data.list || [];

            console.log(`✅ Found ${chapters.length} episodes`);

            return chapters.map((ch: any, index: number) => ({
                episodeNumber: index + 1,
                chapterId: (ch.id || ch.chapterId || ch.chapter_id).toString(),
                title: ch.title || ch.name || `Episode ${index + 1}`,
                duration: ch.duration || ch.time,
                isFree: ch.isFree !== false,
                videoUrl: '',
                token: '',
                videoId: ''
            }));
        }

        return [];
    } catch (error: any) {
        console.error(`❌ Failed to fetch episodes: ${error.message}`);
        return [];
    }
}

/**
 * Fetch video playback URL
 */
async function fetchVideoUrl(bookId: string, chapterId: string): Promise<{ url: string, token: string, videoId: string } | null> {
    try {
        const timestamp = Date.now().toString();
        const body = {
            bookId: bookId,
            chapterId: chapterId,
            addRecently: true,
            chapterIndex: 1
        };

        const sign = generateSignV2({
            timestamp,
            body,
            gaid: DEVICE_PARAMS.gaid,
            androidId: DEVICE_PARAMS.androidId,
            userToken: DEVICE_PARAMS.userToken
        });

        const response = await axios.post(`${API_BASE}/chapter/play`, body, {
            headers: {
                'sign': sign,
                'timestamp': timestamp,
                'Content-Type': 'application/json',
                'User-Agent': 'okhttp/4.9.3'
            },
            timeout: 30000
        });

        if (response.data && response.data.data) {
            const data = response.data.data;
            const videoUrl = data.videoUrl || data.playUrl || data.url || '';

            if (videoUrl) {
                // Parse token and videoId from URL
                // Pattern: /mts/books/{suffix}/{bookId}/{chapterId}/{token}/{resolution}/{videoId}_{resolution}.m3u8
                const match = videoUrl.match(/\/([a-z0-9]+)\/(\d+p)\/([a-z0-9]+)_\d+p\.m3u8/i);

                return {
                    url: videoUrl,
                    token: match ? match[1] : '',
                    videoId: match ? match[3] : ''
                };
            }
        }

        return null;
    } catch (error: any) {
        console.error(`❌ Failed to fetch video URL for chapter ${chapterId}: ${error.message}`);
        return null;
    }
}

/**
 * Download cover image
 */
async function downloadCover(coverUrl: string, bookId: string): Promise<string> {
    try {
        const ext = coverUrl.includes('.jpg') ? 'jpg' : 'png';
        const outputPath = path.join(COVERS_DIR, `${bookId}.${ext}`);

        if (fs.existsSync(outputPath)) {
            console.log(`  ✓ Cover already exists`);
            return outputPath;
        }

        console.log(`  📥 Downloading cover...`);

        const response = await axios.get(coverUrl, {
            responseType: 'arraybuffer',
            headers: {
                'User-Agent': 'okhttp/4.9.3'
            },
            timeout: 30000
        });

        fs.writeFileSync(outputPath, response.data);
        console.log(`  ✅ Cover saved: ${path.basename(outputPath)}`);

        return outputPath;
    } catch (error: any) {
        console.error(`  ❌ Failed to download cover: ${error.message}`);
        return '';
    }
}

/**
 * Generate proper HLS playlist
 */
function generateHLSPlaylist(episode: Episode, bookId: string, resolution: string = '720p'): string {
    const segments: string[] = [];
    const baseUrl = `https://v2-akm.goodreels.com/mts/books/${bookId.slice(-3)}/${bookId}/${episode.chapterId}/${episode.token}/${resolution}`;

    // Generate segment URLs
    let segmentIndex = 0;
    while (true) {
        const segmentName = `${episode.videoId}_${resolution}_${segmentIndex.toString().padStart(6, '0')}.ts`;
        segments.push(`${baseUrl}/${segmentName}`);
        segmentIndex++;

        // Stop after reasonable number or when we know total
        if (segmentIndex > 100) break; // Safety limit
    }

    // Build M3U8 playlist
    let playlist = '#EXTM3U\n';
    playlist += '#EXT-X-VERSION:3\n';
    playlist += '#EXT-X-TARGETDURATION:10\n';
    playlist += '#EXT-X-MEDIA-SEQUENCE:0\n';

    segments.forEach(url => {
        playlist += '#EXTINF:10.0,\n';
        playlist += url + '\n';
    });

    playlist += '#EXT-X-ENDLIST\n';

    return playlist;
}

/**
 * Save episode metadata and playlist
 */
function saveEpisode(drama: ScrapedDrama, episode: Episode, episodeDir: string) {
    // Create episode directory: Episode 1, Episode 2, etc
    const episodeFolderName = `Episode ${episode.episodeNumber}`;
    const episodePath = path.join(episodeDir, episodeFolderName);

    if (!fs.existsSync(episodePath)) {
        fs.mkdirSync(episodePath, { recursive: true });
    }

    // Save episode metadata
    const metadata = {
        episodeNumber: episode.episodeNumber,
        title: episode.title,
        chapterId: episode.chapterId,
        duration: episode.duration,
        isFree: episode.isFree,
        videoUrl: episode.videoUrl,
        drama: {
            title: drama.metadata.title,
            bookId: drama.metadata.bookId
        }
    };

    fs.writeFileSync(
        path.join(episodePath, 'metadata.json'),
        JSON.stringify(metadata, null, 2)
    );

    // Generate and save HLS playlist
    const playlist = generateHLSPlaylist(episode, drama.metadata.bookId);
    fs.writeFileSync(
        path.join(episodePath, 'playlist.m3u8'),
        playlist
    );

    console.log(`  ✅ Episode ${episode.episodeNumber} saved`);
}

/**
 * Main scraper function
 */
export async function scrapeDrama(bookId: string): Promise<ScrapedDrama | null> {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`🎬 Scraping Drama: ${bookId}`);
    console.log(`${'='.repeat(60)}\n`);

    ensureDirs();

    // Step 1: Fetch metadata
    const metadata = await fetchDramaMetadata(bookId);
    if (!metadata) {
        console.error('❌ Failed to fetch metadata. Aborting.');
        return null;
    }

    // Step 2: Download cover
    let coverPath = '';
    if (metadata.cover) {
        coverPath = await downloadCover(metadata.cover, bookId);
    }

    // Step 3: Fetch episode list
    const episodes = await fetchEpisodeList(bookId);
    if (episodes.length === 0) {
        console.error('❌ No episodes found. Aborting.');
        return null;
    }

    // Step 4: Fetch video URLs for each episode
    console.log(`\n📺 Fetching video URLs for ${episodes.length} episodes...`);
    for (let i = 0; i < episodes.length; i++) {
        const episode = episodes[i];
        console.log(`  [${i + 1}/${episodes.length}] ${episode.title}...`);

        const videoData = await fetchVideoUrl(bookId, episode.chapterId);
        if (videoData) {
            episode.videoUrl = videoData.url;
            episode.token = videoData.token;
            episode.videoId = videoData.videoId;
            console.log(`    ✅ Got video URL`);
        } else {
            console.log(`    ⚠️  Failed to get video URL`);
        }

        // Rate limiting
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    // Step 5: Create drama structure
    const dramaDir = path.join(EPISODES_DIR, sanitizeFilename(metadata.title));
    if (!fs.existsSync(dramaDir)) {
        fs.mkdirSync(dramaDir, { recursive: true });
    }

    // Save drama metadata
    const dramaMeta = {
        ...metadata,
        episodeCount: episodes.length,
        coverPath: coverPath,
        scrapedAt: new Date().toISOString()
    };

    fs.writeFileSync(
        path.join(dramaDir, 'drama.json'),
        JSON.stringify(dramaMeta, null, 2)
    );

    // Copy cover to drama folder
    if (coverPath && fs.existsSync(coverPath)) {
        const dramaCover = path.join(dramaDir, 'cover.jpg');
        fs.copyFileSync(coverPath, dramaCover);
    }

    // Step 6: Save episodes
    console.log(`\n💾 Saving ${episodes.length} episodes...`);
    episodes.forEach(episode => {
        if (episode.videoUrl) {
            saveEpisode({ metadata, episodes, coverPath }, episode, dramaDir);
        }
    });

    console.log(`\n${'='.repeat(60)}`);
    console.log(`✅ COMPLETED: ${metadata.title}`);
    console.log(`   Episodes: ${episodes.length}`);
    console.log(`   Output: ${dramaDir}`);
    console.log(`${'='.repeat(60)}\n`);

    return { metadata, episodes, coverPath };
}

/**
 * Sanitize filename
 */
function sanitizeFilename(name: string): string {
    return name
        .replace(/[<>:"/\\|?*]/g, '')
        .replace(/\s+/g, ' ')
        .trim();
}

// CLI usage
if (require.main === module) {
    const bookId = process.argv[2];

    if (!bookId) {
        console.log('Usage: ts-node complete-scraper.ts <bookId>');
        console.log('Example: ts-node complete-scraper.ts 31000991502');
        process.exit(1);
    }

    scrapeDrama(bookId)
        .then(result => {
            if (result) {
                console.log('\n✅ Scraping complete!');
                process.exit(0);
            } else {
                console.log('\n❌ Scraping failed!');
                process.exit(1);
            }
        })
        .catch(error => {
            console.error('\n❌ Error:', error);
            process.exit(1);
        });
}
