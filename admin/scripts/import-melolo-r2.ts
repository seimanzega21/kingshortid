import 'dotenv/config';
import { PrismaClient } from '@prisma/client';
import { S3Client, ListObjectsV2Command, GetObjectCommand } from '@aws-sdk/client-s3';

const prisma = new PrismaClient();

const R2_ENDPOINT = process.env.R2_ENDPOINT!;
const R2_ACCESS_KEY_ID = process.env.R2_ACCESS_KEY_ID!;
const R2_SECRET_ACCESS_KEY = process.env.R2_SECRET_ACCESS_KEY!;
const R2_BUCKET = process.env.R2_BUCKET_NAME || 'shortlovers';
const R2_PUBLIC_URL = process.env.R2_PUBLIC_URL || 'https://stream.shortlovers.id';

const s3 = new S3Client({
    region: 'auto',
    endpoint: R2_ENDPOINT,
    credentials: {
        accessKeyId: R2_ACCESS_KEY_ID,
        secretAccessKey: R2_SECRET_ACCESS_KEY,
    },
});

interface MeloloMetadata {
    source: string;
    series_id: string;
    title: string;
    slug: string;
    author: string;
    description: string;
    genres: string[];
    total_episodes: number;
    captured_episodes: number;
    format?: string; // 'mp4' or undefined (HLS)
    cover: string;
    cover_url: string;
    episodes: { number: number; path: string }[];
}

/**
 * List all melolo drama slugs on R2
 */
async function listMeloloDramas(): Promise<string[]> {
    const slugs = new Set<string>();
    let token: string | undefined;

    do {
        const cmd = new ListObjectsV2Command({
            Bucket: R2_BUCKET,
            Prefix: 'melolo/',
            Delimiter: '/',
            ContinuationToken: token,
        });
        const resp = await s3.send(cmd);
        for (const prefix of resp.CommonPrefixes || []) {
            if (prefix.Prefix) {
                const slug = prefix.Prefix.replace('melolo/', '').replace('/', '');
                if (slug) slugs.add(slug);
            }
        }
        token = resp.NextContinuationToken;
    } while (token);

    return [...slugs].sort();
}

/**
 * Read metadata.json from R2 for a drama
 */
async function readMetadata(slug: string): Promise<MeloloMetadata | null> {
    try {
        const cmd = new GetObjectCommand({
            Bucket: R2_BUCKET,
            Key: `melolo/${slug}/metadata.json`,
        });
        const resp = await s3.send(cmd);
        const body = await resp.Body?.transformToString('utf-8');
        if (!body) return null;
        return JSON.parse(body);
    } catch {
        return null;
    }
}

/**
 * Check if drama has cover on R2
 */
async function hasCoverOnR2(slug: string): Promise<string | null> {
    // Check poster.jpg first (JPEG-converted covers), then cover.*
    for (const prefix of [`melolo/${slug}/poster.`, `melolo/${slug}/cover.`]) {
        try {
            const cmd = new ListObjectsV2Command({
                Bucket: R2_BUCKET,
                Prefix: prefix,
                MaxKeys: 1,
            });
            const resp = await s3.send(cmd);
            if ((resp.Contents?.length || 0) > 0) {
                const key = resp.Contents![0].Key!;
                return `${R2_PUBLIC_URL}/${key}`;
            }
        } catch { }
    }
    return null;
}

/**
 * Count actual episodes on R2 (both HLS and MP4)
 */
async function countR2Episodes(slug: string): Promise<{ hls: number; mp4: number }> {
    let token: string | undefined;
    const hlsSet = new Set<string>();
    const mp4Set = new Set<string>();

    do {
        const cmd = new ListObjectsV2Command({
            Bucket: R2_BUCKET,
            Prefix: `melolo/${slug}/episodes/`,
            MaxKeys: 1000,
            ContinuationToken: token,
        });
        const resp = await s3.send(cmd);
        for (const obj of resp.Contents || []) {
            if (!obj.Key) continue;
            // HLS: melolo/slug/episodes/003/playlist.m3u8
            if (obj.Key.endsWith('/playlist.m3u8')) {
                const parts = obj.Key.split('/');
                hlsSet.add(parts[parts.length - 2]); // episode folder number
            }
            // MP4: melolo/slug/episodes/003.mp4
            if (obj.Key.endsWith('.mp4')) {
                const fname = obj.Key.split('/').pop()!;
                mp4Set.add(fname.replace('.mp4', ''));
            }
        }
        token = resp.NextContinuationToken;
    } while (token);

    return { hls: hlsSet.size, mp4: mp4Set.size };
}

/**
 * Build video URL based on format
 */
function buildVideoUrl(slug: string, epPath: string): string {
    return `${R2_PUBLIC_URL}/melolo/${slug}/${epPath}`;
}

function buildCoverUrl(slug: string): string {
    return `${R2_PUBLIC_URL}/melolo/${slug}/cover.jpg`;
}

/**
 * Import a single drama + episodes into the database
 */
async function importDrama(meta: MeloloMetadata, index: number, total: number): Promise<{
    dramaCreated: boolean;
    episodesCreated: number;
    episodesUpdated: number;
}> {
    const result = { dramaCreated: false, episodesCreated: 0, episodesUpdated: 0 };

    console.log(`\n  [${index}/${total}] ${meta.title}`);

    // Use actual cover URL from R2 (prefers poster.jpg over cover.jpg)
    const coverUrl = await hasCoverOnR2(meta.slug) || buildCoverUrl(meta.slug);

    // Upsert drama by title (or slug matching)
    let drama = await prisma.drama.findFirst({
        where: {
            OR: [
                { title: meta.title },
                { title: { contains: meta.slug.replace(/-/g, ' '), mode: 'insensitive' } },
            ],
        },
    });

    if (drama) {
        // Update existing
        await prisma.drama.update({
            where: { id: drama.id },
            data: {
                cover: coverUrl,
                description: meta.description || drama.description,
                genres: meta.genres.length > 0 ? meta.genres : drama.genres,
                totalEpisodes: Math.max(meta.captured_episodes, drama.totalEpisodes),
                status: 'completed',
                country: 'China',
                language: 'Indonesia',
            },
        });
        console.log(`    Updated drama (ID: ${drama.id})`);
    } else {
        // Create new
        drama = await prisma.drama.create({
            data: {
                title: meta.title,
                description: meta.description || `Drama pendek: ${meta.title}`,
                cover: coverUrl,
                genres: meta.genres.length > 0 ? meta.genres : ['Drama'],
                totalEpisodes: meta.captured_episodes,
                rating: parseFloat((4.0 + Math.random() * 0.9).toFixed(1)),
                views: Math.floor(Math.random() * 5000) + 500,
                status: 'completed',
                country: 'China',
                language: 'Indonesia',
            },
        });
        result.dramaCreated = true;
        console.log(`    Created drama (ID: ${drama.id})`);
    }

    // Delete existing episodes to re-number cleanly
    await prisma.episode.deleteMany({ where: { dramaId: drama.id } });

    // Import episodes — renumber sequentially from 1
    const sortedEps = [...meta.episodes].sort((a, b) => a.number - b.number);
    for (let i = 0; i < sortedEps.length; i++) {
        const ep = sortedEps[i];
        const displayNumber = i + 1; // Always start from 1
        const videoUrl = buildVideoUrl(meta.slug, ep.path);

        await prisma.episode.create({
            data: {
                dramaId: drama.id,
                episodeNumber: displayNumber,
                title: `Episode ${displayNumber}`,
                description: `${meta.title} - Episode ${displayNumber}`,
                videoUrl,
                duration: 180,
                isVip: false,
                coinPrice: 0,
            },
        });
        result.episodesCreated++;
    }

    console.log(`    Episodes: ${result.episodesCreated} created, ${result.episodesUpdated} updated`);
    return result;
}

/**
 * Main
 */
async function main() {
    console.log('='.repeat(60));
    console.log('  MELOLO R2 → DATABASE IMPORT');
    console.log('='.repeat(60));
    console.log(`\n  R2 Bucket: ${R2_BUCKET}`);
    console.log(`  Public URL: ${R2_PUBLIC_URL}`);

    // List all melolo dramas on R2
    console.log('\n  Scanning R2 for melolo dramas...');
    const slugs = await listMeloloDramas();
    console.log(`  Found ${slugs.length} drama folders on R2`);

    let totalCreated = 0;
    let totalUpdated = 0;
    let totalEpCreated = 0;
    let totalEpUpdated = 0;
    let skipped = 0;
    let noMeta = 0;

    for (let i = 0; i < slugs.length; i++) {
        const slug = slugs[i];

        // Read metadata from R2
        const meta = await readMetadata(slug);
        if (!meta) {
            console.log(`\n  [${i + 1}/${slugs.length}] ${slug} — SKIP: no metadata.json`);
            noMeta++;
            continue;
        }

        if (!meta.episodes || meta.episodes.length === 0) {
            console.log(`\n  [${i + 1}/${slugs.length}] ${meta.title} — SKIP: 0 episodes`);
            skipped++;
            continue;
        }

        try {
            const result = await importDrama(meta, i + 1, slugs.length);
            if (result.dramaCreated) totalCreated++;
            else totalUpdated++;
            totalEpCreated += result.episodesCreated;
            totalEpUpdated += result.episodesUpdated;
        } catch (error: any) {
            console.error(`\n  [${i + 1}/${slugs.length}] ${meta.title} — ERROR: ${error.message}`);
        }
    }

    console.log('\n' + '='.repeat(60));
    console.log('  IMPORT COMPLETE');
    console.log('='.repeat(60));
    console.log(`  Dramas created:  ${totalCreated}`);
    console.log(`  Dramas updated:  ${totalUpdated}`);
    console.log(`  Episodes created: ${totalEpCreated}`);
    console.log(`  Episodes updated: ${totalEpUpdated}`);
    console.log(`  Skipped (empty):  ${skipped}`);
    console.log(`  No metadata:      ${noMeta}`);
    console.log('='.repeat(60));

    await prisma.$disconnect();
}

main()
    .then(() => process.exit(0))
    .catch((err) => {
        console.error('Fatal:', err);
        process.exit(1);
    });
