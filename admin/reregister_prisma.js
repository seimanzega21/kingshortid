// Re-register episodes from R2 to DB via Prisma
// Usage: node reregister_prisma.js
const { PrismaClient } = require('@prisma/client');
const { S3Client, ListObjectsV2Command } = require('@aws-sdk/client-s3');
require('dotenv').config();

const prisma = new PrismaClient();

const s3 = new S3Client({
    endpoint: process.env.R2_ENDPOINT,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
    },
    region: 'auto',
});

const BUCKET = 'shortlovers';
const R2_PUBLIC = 'https://stream.shortlovers.id';

function slugify(text) {
    return text.toLowerCase().trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_]+/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
}

async function listR2Files(prefix) {
    const files = [];
    let continuationToken;

    do {
        const cmd = new ListObjectsV2Command({
            Bucket: BUCKET,
            Prefix: prefix,
            ContinuationToken: continuationToken,
        });
        const res = await s3.send(cmd);
        if (res.Contents) {
            for (const obj of res.Contents) {
                files.push(obj.Key);
            }
        }
        continuationToken = res.NextContinuationToken;
    } while (continuationToken);

    return files;
}

async function getR2Episodes(slug) {
    const prefix = `melolo/${slug}/`;
    const files = await listR2Files(prefix);
    const episodes = {};

    for (const key of files) {
        const rel = key.substring(prefix.length);

        // HLS: episodes/{num}/playlist.m3u8
        let m = rel.match(/^episodes\/(\d+)\/playlist\.m3u8$/);
        if (m) {
            const num = parseInt(m[1]);
            if (!episodes[num]) episodes[num] = `${R2_PUBLIC}/${key}`;
            continue;
        }

        // HLS: ep{num}/playlist.m3u8
        m = rel.match(/^ep(\d+)\/playlist\.m3u8$/);
        if (m) {
            const num = parseInt(m[1]);
            if (!episodes[num]) episodes[num] = `${R2_PUBLIC}/${key}`;
            continue;
        }

        // MP4: ep001.mp4
        m = rel.match(/^ep(\d+)\.mp4$/);
        if (m) {
            const num = parseInt(m[1]);
            if (!episodes[num]) episodes[num] = `${R2_PUBLIC}/${key}`;
        }
    }

    return Object.entries(episodes)
        .map(([num, url]) => ({ num: parseInt(num), url }))
        .sort((a, b) => a.num - b.num);
}

async function main() {
    console.log('='.repeat(65));
    console.log('  RE-REGISTER R2 EPISODES -> DB (via Prisma)');
    console.log('='.repeat(65));

    // 1. Find dramas with 0 episodes
    const allDramas = await prisma.drama.findMany({
        where: { isActive: true },
        include: { _count: { select: { episodes: true } } },
    });

    const missing = allDramas.filter(d => d._count.episodes === 0);
    console.log(`\nTotal dramas: ${allDramas.length}`);
    console.log(`Missing episodes: ${missing.length}\n`);

    if (missing.length === 0) {
        console.log('Nothing to do!');
        return;
    }

    let totalOk = 0;
    let totalFail = 0;

    for (let i = 0; i < missing.length; i++) {
        const drama = missing[i];
        const slug = slugify(drama.title);
        console.log(`\n[${i + 1}/${missing.length}] ${drama.title}`);
        console.log(`  Slug: ${slug}`);

        // Scan R2
        const r2Eps = await getR2Episodes(slug);
        if (r2Eps.length === 0) {
            console.log(`  [MISS] No episodes on R2`);
            continue;
        }

        console.log(`  Found ${r2Eps.length} episodes on R2`);

        // Batch create episodes via Prisma
        let ok = 0;
        let fail = 0;

        for (const ep of r2Eps) {
            try {
                await prisma.episode.create({
                    data: {
                        dramaId: drama.id,
                        episodeNumber: ep.num,
                        title: `Episode ${ep.num}`,
                        videoUrl: ep.url,
                        duration: 0,
                        isVip: false,
                        coinPrice: 0,
                    },
                });
                ok++;
            } catch (e) {
                fail++;
                if (fail <= 2) {
                    console.log(`    FAIL ep${ep.num}: ${e.message.substring(0, 80)}`);
                }
            }
        }

        // Update totalEpisodes on drama
        if (ok > 0) {
            await prisma.drama.update({
                where: { id: drama.id },
                data: { totalEpisodes: ok },
            });
        }

        console.log(`  OK: ${ok}, FAIL: ${fail}`);
        totalOk += ok;
        totalFail += fail;
    }

    console.log(`\n${'='.repeat(65)}`);
    console.log(`  DONE: Registered ${totalOk} episodes, Failed ${totalFail}`);
    console.log('='.repeat(65));

    await prisma.$disconnect();
}

main().catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
});
