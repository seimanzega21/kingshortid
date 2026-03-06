/**
 * Backfill: Register R2 dramas + episodes directly via Prisma (no rate limits)
 */
const { PrismaClient } = require('@prisma/client');
const { S3Client, ListObjectsV2Command } = require('@aws-sdk/client-s3');
require('dotenv').config();

const p = new PrismaClient();
const R2_PUBLIC = process.env.R2_PUBLIC_URL || 'https://stream.shortlovers.id';

const s3 = new S3Client({
    region: 'auto',
    endpoint: process.env.R2_ENDPOINT,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
    },
});
const BUCKET = process.env.R2_BUCKET_NAME;

function slugToTitle(slug) {
    return slug.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

async function listR2Dramas(prefix) {
    const slugs = new Set();
    let token;
    do {
        const res = await s3.send(new ListObjectsV2Command({
            Bucket: BUCKET, Prefix: prefix, Delimiter: '/', ContinuationToken: token,
        }));
        for (const cp of (res.CommonPrefixes || [])) {
            const slug = cp.Prefix.replace(prefix, '').replace(/\/$/, '');
            if (slug) slugs.add(slug);
        }
        token = res.NextContinuationToken;
    } while (token);
    return [...slugs];
}

async function getEpisodeFiles(prefix, slug) {
    const episodes = [];
    let token;
    do {
        const res = await s3.send(new ListObjectsV2Command({
            Bucket: BUCKET, Prefix: `${prefix}${slug}/`, ContinuationToken: token,
        }));
        for (const obj of (res.Contents || [])) {
            const mp4 = obj.Key.match(/ep(\d+)\.mp4$/);
            const hls = obj.Key.match(/ep(\d+)\/playlist\.m3u8$/);
            if (mp4) episodes.push({ number: parseInt(mp4[1]), videoUrl: `${R2_PUBLIC}/${obj.Key}` });
            else if (hls) episodes.push({ number: parseInt(hls[1]), videoUrl: `${R2_PUBLIC}/${obj.Key}` });
        }
        token = res.NextContinuationToken;
    } while (token);
    return episodes.sort((a, b) => a.number - b.number);
}

async function main() {
    console.log('🔍 Scanning R2 for dramas...\n');

    const melolo = await listR2Dramas('melolo/');
    const vidrama = await listR2Dramas('vidrama/');
    const microdrama = await listR2Dramas('microdrama/');
    console.log(`Found ${melolo.length} melolo + ${vidrama.length} vidrama + ${microdrama.length} microdrama in R2`);

    const dbDramas = await p.drama.findMany({ select: { id: true, title: true } });
    const existingMap = new Map(dbDramas.map(d => [d.title.toLowerCase(), d.id]));

    const all = [
        ...melolo.map(s => ({ slug: s, prefix: 'melolo/' })),
        ...vidrama.map(s => ({ slug: s, prefix: 'vidrama/' })),
        ...microdrama.map(s => ({ slug: s, prefix: 'microdrama/' })),
    ];

    let registered = 0, skipped = 0, failed = 0, epsAdded = 0;

    for (const { slug, prefix } of all) {
        const title = slugToTitle(slug);

        if (existingMap.has(title.toLowerCase())) {
            // Drama exists — check if episodes are missing
            const dramaId = existingMap.get(title.toLowerCase());
            const dbEpCount = await p.episode.count({ where: { dramaId } });
            const r2Episodes = await getEpisodeFiles(prefix, slug);

            if (r2Episodes.length > dbEpCount) {
                // Register missing episodes
                let added = 0;
                for (const ep of r2Episodes) {
                    try {
                        await p.episode.upsert({
                            where: { dramaId_episodeNumber: { dramaId, episodeNumber: ep.number } },
                            update: { videoUrl: ep.videoUrl },
                            create: {
                                dramaId, episodeNumber: ep.number,
                                title: `Episode ${ep.number}`, videoUrl: ep.videoUrl,
                                isActive: true, isVip: false, coinPrice: 0, views: 0, duration: 0,
                            },
                        });
                        added++;
                    } catch { }
                }
                if (added > dbEpCount) {
                    await p.drama.update({ where: { id: dramaId }, data: { totalEpisodes: r2Episodes.length } });
                    console.log(`  🔄 ${title}: +${added - dbEpCount} new eps (${dbEpCount}→${r2Episodes.length})`);
                    epsAdded += (added - dbEpCount);
                }
            }
            skipped++;
            continue;
        }

        const episodes = await getEpisodeFiles(prefix, slug);
        if (episodes.length === 0) { skipped++; continue; }

        try {
            // Create drama directly via Prisma
            const drama = await p.drama.create({
                data: {
                    title, description: title,
                    cover: `${R2_PUBLIC}/${prefix}${slug}/cover.webp`,
                    genres: ['Drama'], status: 'completed', country: 'China', language: 'Indonesia',
                    isActive: true, views: 0, rating: 0, totalEpisodes: episodes.length,
                },
            });

            // Batch insert episodes
            await p.episode.createMany({
                data: episodes.map(ep => ({
                    dramaId: drama.id, episodeNumber: ep.number,
                    title: `Episode ${ep.number}`, videoUrl: ep.videoUrl,
                    isActive: true, isVip: false, coinPrice: 0, views: 0, duration: 0,
                })),
                skipDuplicates: true,
            });

            console.log(`  ✅ ${title}: ${episodes.length} eps`);
            registered++;
            existingMap.set(title.toLowerCase(), drama.id);
        } catch (e) {
            console.log(`  ❌ ${title}: ${e.message.slice(0, 80)}`);
            failed++;
        }
    }

    console.log(`\n📊 Summary:`);
    console.log(`  ✅ New dramas registered: ${registered}`);
    console.log(`  🔄 Episodes backfilled: ${epsAdded}`);
    console.log(`  ⏭️  Skipped: ${skipped}`);
    console.log(`  ❌ Failed: ${failed}`);

    const td = await p.drama.count({ where: { isActive: true } });
    const te = await p.episode.count({ where: { isActive: true } });
    console.log(`\n  DB Total: ${td} dramas, ${te} episodes`);
    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
