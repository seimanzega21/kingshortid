import { PrismaClient } from '@prisma/client';
import { ListObjectsV2Command, PutObjectCommand } from '@aws-sdk/client-s3';
import { r2Client, R2_BUCKET } from '../config/r2';

const prisma = new PrismaClient();

// R2 Public URL base - update after setting up public bucket
const R2_PUBLIC_BASE = process.env.R2_PUBLIC_URL || 'https://pub-shortlovers.r2.dev';

interface DramaInfo {
    folderName: string;
    title: string;
    episodes: EpisodeInfo[];
    totalFiles: number;
}

interface EpisodeInfo {
    episodeNumber: number;
    folderPath: string;
    coverPath: string | null;
    videoSegments: string[];
}

/**
 * Convert folder name to readable title
 */
function folderToTitle(folder: string): string {
    return folder
        .replace(/^\[sulih_suara\]_/, '') // Remove [sulih_suara] prefix
        .replace(/_/g, ' ')               // Replace underscores with spaces
        .replace(/,/g, ', ')              // Add space after commas
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

/**
 * Extract episode number from folder name
 */
function extractEpisodeNumber(folderName: string): number {
    const match = folderName.match(/_ep_(\d+)/);
    return match ? parseInt(match[1], 10) : 0;
}

/**
 * Scan R2 bucket and organize by drama/episode
 */
async function scanBucketStructure(): Promise<Map<string, DramaInfo>> {
    console.log('🔍 Scanning R2 bucket structure...');

    const dramas = new Map<string, DramaInfo>();
    let continuationToken: string | undefined;
    let totalScanned = 0;

    do {
        const command = new ListObjectsV2Command({
            Bucket: R2_BUCKET,
            MaxKeys: 1000,
            ContinuationToken: continuationToken,
        });

        const response = await r2Client.send(command);
        totalScanned += response.Contents?.length || 0;

        for (const item of response.Contents || []) {
            if (!item.Key) continue;

            const parts = item.Key.split('/');
            if (parts.length < 2) continue;

            const dramaFolder = parts[0];
            const episodeFolder = parts[1];
            const fileName = parts[2] || '';

            // Initialize drama if not exists
            if (!dramas.has(dramaFolder)) {
                dramas.set(dramaFolder, {
                    folderName: dramaFolder,
                    title: folderToTitle(dramaFolder),
                    episodes: [],
                    totalFiles: 0,
                });
            }

            const drama = dramas.get(dramaFolder)!;
            drama.totalFiles++;

            // Extract episode number
            const epNum = extractEpisodeNumber(episodeFolder);
            if (epNum === 0) continue;

            // Find or create episode
            let episode = drama.episodes.find(e => e.episodeNumber === epNum);
            if (!episode) {
                episode = {
                    episodeNumber: epNum,
                    folderPath: `${dramaFolder}/${episodeFolder}`,
                    coverPath: null,
                    videoSegments: [],
                };
                drama.episodes.push(episode);
            }

            // Categorize file
            if (fileName === 'cover.jpg' || fileName === 'cover.png') {
                episode.coverPath = item.Key;
            } else if (fileName.endsWith('.ts')) {
                episode.videoSegments.push(item.Key);
            }
        }

        continuationToken = response.NextContinuationToken;
        console.log(`   📄 Scanned ${totalScanned} objects...`);

    } while (continuationToken);

    // Sort episodes
    dramas.forEach(drama => {
        drama.episodes.sort((a, b) => a.episodeNumber - b.episodeNumber);
    });

    return dramas;
}

/**
 * Generate M3U8 playlist content for HLS streaming
 */
function generateM3U8(segments: string[], duration: number = 10): string {
    const sortedSegments = [...segments].sort();

    let m3u8 = '#EXTM3U\n';
    m3u8 += '#EXT-X-VERSION:3\n';
    m3u8 += `#EXT-X-TARGETDURATION:${duration}\n`;
    m3u8 += '#EXT-X-MEDIA-SEQUENCE:0\n';
    m3u8 += '#EXT-X-PLAYLIST-TYPE:VOD\n\n';

    for (const segment of sortedSegments) {
        const fileName = segment.split('/').pop();
        m3u8 += `#EXTINF:${duration}.0,\n`;
        m3u8 += `${R2_PUBLIC_BASE}/${segment}\n`;
    }

    m3u8 += '#EXT-X-ENDLIST\n';
    return m3u8;
}

/**
 * Get public URL for R2 asset
 */
function getPublicUrl(key: string | null): string | null {
    if (!key) return null;
    return `${R2_PUBLIC_BASE}/${key}`;
}

/**
 * Import dramas from scanned structure to database
 */
async function importToDatabase(dramas: Map<string, DramaInfo>) {
    console.log('\n📊 Importing to database...\n');

    let dramasImported = 0;
    let episodesImported = 0;
    let dramasUpdated = 0;

    for (const [folderName, dramaInfo] of dramas) {
        try {
            console.log(`\n🎬 Processing: ${dramaInfo.title}`);
            console.log(`   📁 Folder: ${folderName}`);
            console.log(`   📺 Episodes: ${dramaInfo.episodes.length}`);

            // Check if drama exists
            let drama = await prisma.drama.findFirst({
                where: { title: dramaInfo.title },
            });

            // Get cover from first episode
            const firstEpisode = dramaInfo.episodes[0];
            const coverUrl = getPublicUrl(firstEpisode?.coverPath) ||
                `https://placehold.co/400x600/1f2937/f59e0b?text=${encodeURIComponent(dramaInfo.title)}`;

            if (drama) {
                // Update existing
                await prisma.drama.update({
                    where: { id: drama.id },
                    data: {
                        cover: coverUrl,
                        totalEpisodes: dramaInfo.episodes.length,
                        updatedAt: new Date(),
                    },
                });
                dramasUpdated++;
                console.log(`   🔄 Updated drama`);
            } else {
                // Create new
                drama = await prisma.drama.create({
                    data: {
                        title: dramaInfo.title,
                        description: `Drama pendek Indonesia: ${dramaInfo.title}. Terdiri dari ${dramaInfo.episodes.length} episode.`,
                        cover: coverUrl,
                        genres: ['Drama', 'Romance'],
                        totalEpisodes: dramaInfo.episodes.length,
                        rating: 4.0 + Math.random(),
                        status: 'completed',
                        country: 'Indonesia',
                        language: 'Indonesia',
                    },
                });
                dramasImported++;
                console.log(`   ✅ Created drama (ID: ${drama.id})`);
            }

            // Import episodes
            for (const epInfo of dramaInfo.episodes) {
                // Check if episode exists
                const existingEp = await prisma.episode.findUnique({
                    where: {
                        dramaId_episodeNumber: {
                            dramaId: drama.id,
                            episodeNumber: epInfo.episodeNumber,
                        },
                    },
                });

                // Generate and upload M3U8
                let videoUrl = '';
                if (epInfo.videoSegments.length > 0) {
                    const m3u8Content = generateM3U8(epInfo.videoSegments);
                    const playlistKey = `${epInfo.folderPath}/playlist.m3u8`;

                    try {
                        await r2Client.send(new PutObjectCommand({
                            Bucket: R2_BUCKET,
                            Key: playlistKey,
                            Body: m3u8Content,
                            ContentType: 'application/vnd.apple.mpegurl', // Standard HLS MIME type
                        }));
                        videoUrl = getPublicUrl(playlistKey)!;
                        // console.log(`      ✅ Playlist created: ${videoUrl}`);
                    } catch (err: any) {
                        console.error(`      ❌ Failed to upload playlist: ${err.message}`);
                        // Fallback to first segment
                        videoUrl = getPublicUrl(epInfo.videoSegments[0])!;
                    }
                }

                const thumbnailUrl = getPublicUrl(epInfo.coverPath);

                if (existingEp) {
                    await prisma.episode.update({
                        where: { id: existingEp.id },
                        data: {
                            thumbnail: thumbnailUrl,
                            videoUrl: videoUrl,
                        },
                    });
                } else {
                    await prisma.episode.create({
                        data: {
                            dramaId: drama.id,
                            episodeNumber: epInfo.episodeNumber,
                            title: `Episode ${epInfo.episodeNumber}`,
                            description: `${dramaInfo.title} - Episode ${epInfo.episodeNumber}`,
                            thumbnail: thumbnailUrl,
                            videoUrl: videoUrl,
                            duration: epInfo.videoSegments.length * 10, // Estimate: 10 sec per segment
                        },
                    });
                    episodesImported++;
                }
            }

            console.log(`   📺 ${dramaInfo.episodes.length} episodes synced`);

        } catch (error: any) {
            console.error(`   ❌ Error: ${error.message}`);
        }
    }

    return { dramasImported, episodesImported, dramasUpdated };
}

/**
 * Main import function
 */
async function main() {
    console.log('='.repeat(60));
    console.log('📦 R2 BUCKET TO DATABASE IMPORT');
    console.log('='.repeat(60));
    console.log(`\n🪣 Bucket: ${R2_BUCKET}`);
    console.log(`🔗 Public URL: ${R2_PUBLIC_BASE}\n`);

    try {
        // Scan bucket
        const dramas = await scanBucketStructure();

        console.log('\n' + '='.repeat(60));
        console.log('📊 SCAN RESULTS');
        console.log('='.repeat(60));
        console.log(`\n🎬 Total Dramas: ${dramas.size}`);

        let totalEpisodes = 0;
        dramas.forEach(d => totalEpisodes += d.episodes.length);
        console.log(`📺 Total Episodes: ${totalEpisodes}`);

        // Import to database
        const results = await importToDatabase(dramas);

        // Summary
        console.log('\n' + '='.repeat(60));
        console.log('📊 IMPORT SUMMARY');
        console.log('='.repeat(60));
        console.log(`\n✅ Dramas Created: ${results.dramasImported}`);
        console.log(`🔄 Dramas Updated: ${results.dramasUpdated}`);
        console.log(`📺 Episodes Created: ${results.episodesImported}`);
        console.log('\n🎉 Import complete!');

    } catch (error: any) {
        console.error('\n❌ Fatal error:', error.message);
        throw error;
    } finally {
        await prisma.$disconnect();
    }
}

// Run
main()
    .then(() => process.exit(0))
    .catch(() => process.exit(1));
