/**
 * BULK REGISTER R2 DRAMAS TO DATABASE
 * ====================================
 * Scans R2 for dramas not in DB, reads metadata from R2,
 * verifies completeness, and registers via Prisma direct.
 *
 * Handles both MP4 and HLS formats.
 *
 * Usage:
 *   node register_all_r2.js              # Dry run
 *   node register_all_r2.js --execute    # Actually register
 */
const { PrismaClient } = require('@prisma/client');
const { S3Client, ListObjectsV2Command, GetObjectCommand } = require('@aws-sdk/client-s3');
const https = require('https');
require('dotenv').config();

const prisma = new PrismaClient();

const R2_PUBLIC = 'https://stream.shortlovers.id';

const s3 = new S3Client({
    region: 'auto',
    endpoint: process.env.R2_ENDPOINT,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
    },
});
const BUCKET = process.env.R2_BUCKET_NAME;

async function listAllR2Objects(prefix) {
    const objects = [];
    let continuationToken;
    do {
        const cmd = new ListObjectsV2Command({
            Bucket: BUCKET,
            Prefix: prefix,
            ContinuationToken: continuationToken,
        });
        const resp = await s3.send(cmd);
        if (resp.Contents) objects.push(...resp.Contents);
        continuationToken = resp.IsTruncated ? resp.NextContinuationToken : undefined;
    } while (continuationToken);
    return objects;
}

async function getR2Json(key) {
    try {
        const cmd = new GetObjectCommand({ Bucket: BUCKET, Key: key });
        const resp = await s3.send(cmd);
        const body = await resp.Body.transformToString();
        return JSON.parse(body);
    } catch {
        return null;
    }
}

function slugify(text) {
    return text.toLowerCase().trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_]+/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
}

async function main() {
    const execute = process.argv.includes('--execute');

    console.log('='.repeat(65));
    console.log(`  BULK REGISTER R2 DRAMAS TO DATABASE`);
    console.log(`  Mode: ${execute ? '🔴 EXECUTE' : '🟡 DRY RUN'}`);
    console.log('='.repeat(65));

    // Step 1: Get existing DB dramas
    console.log('\n📋 Loading database dramas...');
    const dbDramas = await prisma.drama.findMany({
        select: { id: true, title: true },
    });
    const dbTitles = new Set(dbDramas.map(d => d.title.toLowerCase()));
    const dbSlugs = new Set(dbDramas.map(d => slugify(d.title)));
    console.log(`  Database has ${dbDramas.length} dramas`);

    // Step 2: Scan R2
    console.log('\n📦 Scanning R2 (this takes ~3 minutes)...');
    const allObjects = await listAllR2Objects('melolo/');
    console.log(`  Found ${allObjects.length} objects in R2`);

    // Build drama map from R2
    const r2Dramas = {};
    for (const obj of allObjects) {
        const parts = obj.Key.split('/');
        if (parts.length < 2) continue;
        const slug = parts[1];
        if (!slug || slug.startsWith('_')) continue;

        if (!r2Dramas[slug]) {
            r2Dramas[slug] = { mp4Eps: {}, hlsEps: {}, hasCover: false, metaKey: null };
        }

        if (obj.Key.endsWith('.mp4')) {
            const match = obj.Key.match(/ep(\d+)\.mp4$/);
            if (match) r2Dramas[slug].mp4Eps[parseInt(match[1])] = obj.Key;
        } else if (obj.Key.endsWith('.m3u8') && obj.Key.includes('/ep')) {
            const match = obj.Key.match(/ep(\d+)/);
            if (match) r2Dramas[slug].hlsEps[parseInt(match[1])] = obj.Key;
        } else if (obj.Key.includes('cover')) {
            r2Dramas[slug].hasCover = true;
            // Detect cover extension
            if (obj.Key.endsWith('.jpg')) r2Dramas[slug].coverExt = 'jpg';
            else if (obj.Key.endsWith('.webp')) r2Dramas[slug].coverExt = 'webp';
            else if (obj.Key.endsWith('.png')) r2Dramas[slug].coverExt = 'png';
            else r2Dramas[slug].coverExt = 'webp';
        } else if (obj.Key.endsWith('metadata.json')) {
            r2Dramas[slug].metaKey = obj.Key;
        }
    }

    console.log(`  Built info for ${Object.keys(r2Dramas).length} drama folders`);

    // Step 3: Filter unregistered dramas with episodes
    const toRegister = [];
    for (const [slug, info] of Object.entries(r2Dramas)) {
        if (dbSlugs.has(slug)) continue;

        const mp4Count = Object.keys(info.mp4Eps).length;
        const hlsCount = Object.keys(info.hlsEps).length;
        if (mp4Count === 0 && hlsCount === 0) continue;

        toRegister.push({ slug, info, mp4Count, hlsCount });
    }

    console.log(`\n  Unregistered dramas with episodes: ${toRegister.length}`);

    if (toRegister.length === 0) {
        console.log('  Nothing to register!');
        await prisma.$disconnect();
        return;
    }

    // Step 4: Register
    console.log(`\n${'='.repeat(65)}`);
    console.log(execute ? '  REGISTERING...' : '  DRY RUN — What would be registered:');
    console.log('='.repeat(65));

    let success = 0, failed = 0, skipped = 0;

    for (let i = 0; i < toRegister.length; i++) {
        const { slug, info, mp4Count, hlsCount } = toRegister[i];
        const num = i + 1;

        // Choose format: prefer MP4 over HLS
        const useMP4 = mp4Count >= hlsCount;
        const eps = useMP4 ? info.mp4Eps : info.hlsEps;
        const fmt = useMP4 ? 'MP4' : 'HLS';
        const epCount = Object.keys(eps).length;

        // Read metadata from R2
        let meta = null;
        if (info.metaKey) {
            meta = await getR2Json(info.metaKey);
        }

        // Build title
        let title = slug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        if (meta && meta.title) title = meta.title;

        // Check for exact title match (case insensitive)
        if (dbTitles.has(title.toLowerCase())) {
            skipped++;
            console.log(`  ${String(num).padStart(3)}. ⏭️  ${slug} — already in DB (title match)`);
            continue;
        }

        const description = (meta && (meta.description || meta.desc)) || title;
        const genres = (meta && meta.genres && meta.genres.length > 0) ? meta.genres : ['Drama'];
        const coverExt = info.coverExt || 'webp';
        const coverUrl = `${R2_PUBLIC}/melolo/${slug}/cover.${coverExt}`;

        if (!execute) {
            console.log(`  ${String(num).padStart(3)}. 📋 ${title.substring(0, 40).padEnd(40)} ${String(epCount).padStart(3)} eps [${fmt}] cover:${info.hasCover ? '✅' : '❌'}`);
            success++;
            continue;
        }

        // Execute registration
        try {
            const drama = await prisma.drama.create({
                data: {
                    title,
                    description: description.trim() || title,
                    cover: coverUrl,
                    genres: Array.isArray(genres) ? genres : [],
                    totalEpisodes: epCount,
                    rating: 4.5,
                    views: Math.floor(Math.random() * 3000) + 500,
                    status: 'completed',
                    isActive: true,
                    country: 'China',
                    language: 'Indonesia',
                },
            });

            // Register episodes
            let epFail = 0;
            const sortedEpNums = Object.keys(eps).map(Number).sort((a, b) => a - b);

            for (const epNum of sortedEpNums) {
                const videoUrl = `${R2_PUBLIC}/${eps[epNum]}`;
                try {
                    await prisma.episode.create({
                        data: {
                            dramaId: drama.id,
                            episodeNumber: epNum,
                            title: `Episode ${epNum}`,
                            videoUrl,
                            duration: 0,
                            isActive: true,
                        },
                    });
                } catch (epErr) {
                    epFail++;
                }
            }

            const failNote = epFail > 0 ? ` (${epFail} ep failed)` : '';
            console.log(`  ${String(num).padStart(3)}. ✅ ${title.substring(0, 40).padEnd(40)} ${String(epCount).padStart(3)} eps [${fmt}]${failNote}`);
            success++;
        } catch (err) {
            const msg = err.message || String(err);
            if (msg.includes('Unique constraint')) {
                skipped++;
                console.log(`  ${String(num).padStart(3)}. ⏭️  ${slug} — duplicate title`);
            } else {
                failed++;
                console.log(`  ${String(num).padStart(3)}. ❌ ${slug} — ${msg.substring(0, 80)}`);
            }
        }
    }

    console.log(`\n${'='.repeat(65)}`);
    console.log(`  ${execute ? 'REGISTERED' : 'WOULD REGISTER'}: ${success}`);
    console.log(`  Failed: ${failed}`);
    console.log(`  Skipped (duplicates): ${skipped}`);
    console.log('='.repeat(65));

    if (!execute) {
        console.log('\n  Run with --execute to actually register these dramas.');
    }

    await prisma.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
