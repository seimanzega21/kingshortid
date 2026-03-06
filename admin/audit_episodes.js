/**
 * EPISODE COMPLETENESS AUDIT
 * ===========================
 * Compares episode counts: DB vs R2 vs Vidrama API
 * Finds dramas with missing episodes and reports them.
 *
 * Usage:
 *   node audit_episodes.js                # Audit all dramas
 *   node audit_episodes.js --fix          # Fix missing episodes in R2 + DB
 */
const { PrismaClient } = require('@prisma/client');
const { S3Client, ListObjectsV2Command } = require('@aws-sdk/client-s3');
const https = require('https');
require('dotenv').config();

const prisma = new PrismaClient();
const R2_PUBLIC = 'https://stream.shortlovers.id';
const VIDRAMA_API = 'https://vidrama.asia/api/melolo';

const s3 = new S3Client({
    region: 'auto',
    endpoint: process.env.R2_ENDPOINT,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
    },
});
const BUCKET = process.env.R2_BUCKET_NAME;

function fetchJSON(url) {
    return new Promise((resolve, reject) => {
        const req = https.get(url, { timeout: 15000 }, res => {
            let data = '';
            res.on('data', c => data += c);
            res.on('end', () => {
                try { resolve(JSON.parse(data)); }
                catch (e) { reject(e); }
            });
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    });
}

function slugify(text) {
    return text.toLowerCase().trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_]+/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function countR2Episodes(slug) {
    const mp4s = new Set();
    const hlsEps = new Set();
    let continuationToken;

    do {
        const cmd = new ListObjectsV2Command({
            Bucket: BUCKET,
            Prefix: `melolo/${slug}/`,
            ContinuationToken: continuationToken,
        });
        const resp = await s3.send(cmd);
        for (const obj of (resp.Contents || [])) {
            const key = obj.Key;
            const mp4Match = key.match(/ep(\d+)\.mp4$/);
            if (mp4Match) mp4s.add(parseInt(mp4Match[1]));
            const hlsMatch = key.match(/ep(\d+).*\.m3u8$/);
            if (hlsMatch) hlsEps.add(parseInt(hlsMatch[1]));
        }
        continuationToken = resp.IsTruncated ? resp.NextContinuationToken : undefined;
    } while (continuationToken);

    return { mp4: mp4s.size, hls: hlsEps.size, total: Math.max(mp4s.size, hlsEps.size), mp4Nums: mp4s, hlsNums: hlsEps };
}

async function getVidramaEpisodeCount(title) {
    try {
        const searchUrl = `${VIDRAMA_API}?action=search&keyword=${encodeURIComponent(title)}&limit=10`;
        const searchData = await fetchJSON(searchUrl);
        const items = searchData.data || [];

        // Find best match
        const titleLower = title.toLowerCase();
        let match = items.find(x => x.title.toLowerCase() === titleLower);
        if (!match) match = items.find(x => x.title.toLowerCase().includes(titleLower) || titleLower.includes(x.title.toLowerCase()));
        if (!match && items.length > 0) match = items[0];

        if (!match) return { apiEps: 0, found: false };

        // Get detail for episode count
        const detailUrl = `${VIDRAMA_API}?action=detail&id=${match.id}`;
        const detailData = await fetchJSON(detailUrl);
        const detail = detailData.data || {};
        const episodes = detail.episodes || [];

        return { apiEps: episodes.length, found: true, vidramaId: match.id, vidramaTitle: match.title };
    } catch {
        return { apiEps: 0, found: false };
    }
}

async function main() {
    const doFix = process.argv.includes('--fix');

    console.log('='.repeat(65));
    console.log('  EPISODE COMPLETENESS AUDIT');
    console.log(`  Mode: ${doFix ? '🔧 FIX' : '🔍 AUDIT'}`);
    console.log('='.repeat(65));

    // Get all dramas from DB with episode counts
    console.log('\n📋 Loading dramas from database...');
    const dramas = await prisma.drama.findMany({
        select: { id: true, title: true, totalEpisodes: true },
        where: { isActive: true },
        orderBy: { title: 'asc' },
    });

    // Get actual episode counts from DB
    const episodeCounts = await prisma.episode.groupBy({
        by: ['dramaId'],
        _count: { id: true },
    });
    const dbEpMap = {};
    for (const e of episodeCounts) {
        dbEpMap[e.dramaId] = e._count.id;
    }

    console.log(`  Found ${dramas.length} dramas in DB`);

    // Audit each drama
    const issues = [];
    let checked = 0;

    console.log('\n🔍 Checking each drama against R2 and Vidrama API...\n');
    console.log(`  ${'Title'.padEnd(42)} DB_eps  R2_eps  API_eps  Status`);
    console.log(`  ${'─'.repeat(42)} ──────  ──────  ───────  ──────`);

    for (const drama of dramas) {
        checked++;
        const slug = slugify(drama.title);
        const dbEps = dbEpMap[drama.id] || 0;

        // Count R2 episodes
        const r2 = await countR2Episodes(slug);

        // Check Vidrama API
        const api = await getVidramaEpisodeCount(drama.title);
        await sleep(300); // Rate limit

        const maxAvailable = Math.max(r2.total, api.apiEps);
        let status = '✅ OK';

        if (dbEps < maxAvailable) {
            status = '⚠️ MISSING';
            issues.push({
                id: drama.id,
                title: drama.title,
                slug,
                dbEps,
                r2Eps: r2.total,
                r2Mp4: r2.mp4,
                r2Hls: r2.hls,
                apiEps: api.apiEps,
                apiFound: api.found,
                vidramaId: api.vidramaId,
                missing: maxAvailable - dbEps,
            });
        } else if (dbEps === 0) {
            status = '❌ EMPTY';
            issues.push({
                id: drama.id,
                title: drama.title,
                slug,
                dbEps: 0,
                r2Eps: r2.total,
                r2Mp4: r2.mp4,
                r2Hls: r2.hls,
                apiEps: api.apiEps,
                apiFound: api.found,
                vidramaId: api.vidramaId,
                missing: maxAvailable,
            });
        }

        const shortTitle = drama.title.length > 40 ? drama.title.substring(0, 37) + '...' : drama.title;
        console.log(`  ${shortTitle.padEnd(42)} ${String(dbEps).padStart(4)}    ${String(r2.total).padStart(4)}    ${String(api.apiEps).padStart(5)}    ${status}`);
    }

    // Summary
    console.log(`\n${'='.repeat(65)}`);
    console.log(`  SUMMARY`);
    console.log(`${'='.repeat(65)}`);
    console.log(`  Total dramas checked: ${checked}`);
    console.log(`  Dramas with issues: ${issues.length}`);

    if (issues.length > 0) {
        console.log(`\n  DRAMAS WITH MISSING EPISODES:`);
        console.log(`  ${'Title'.padEnd(40)} DB    R2   API   Missing`);
        console.log(`  ${'─'.repeat(40)} ────  ────  ────  ───────`);
        for (const i of issues) {
            const t = i.title.length > 38 ? i.title.substring(0, 35) + '...' : i.title;
            console.log(`  ${t.padEnd(40)} ${String(i.dbEps).padStart(4)}  ${String(i.r2Eps).padStart(4)}  ${String(i.apiEps).padStart(4)}  ${String(i.missing).padStart(5)}`);
        }
    }

    // Save issues to JSON for follow-up
    const fs = require('fs');
    fs.writeFileSync('episode_audit_result.json', JSON.stringify({
        timestamp: new Date().toISOString(),
        totalChecked: checked,
        issueCount: issues.length,
        issues,
    }, null, 2));
    console.log(`\n  Full report saved to episode_audit_result.json`);

    if (issues.length > 0 && doFix) {
        console.log(`\n${'='.repeat(65)}`);
        console.log(`  FIXING MISSING EPISODES IN DB...`);
        console.log(`${'='.repeat(65)}`);

        let fixed = 0;
        for (const issue of issues) {
            // Get existing episode numbers in DB
            const existingEps = await prisma.episode.findMany({
                where: { dramaId: issue.id },
                select: { episodeNumber: true },
            });
            const existingNums = new Set(existingEps.map(e => e.episodeNumber));

            // Get R2 episode files to know what's available
            const r2 = await countR2Episodes(issue.slug);
            const allR2Nums = new Set([...r2.mp4Nums, ...r2.hlsNums]);

            // Register missing episodes that exist in R2
            let addedCount = 0;
            for (const epNum of [...allR2Nums].sort((a, b) => a - b)) {
                if (existingNums.has(epNum)) continue;

                // Determine video URL
                let videoUrl;
                if (r2.mp4Nums.has(epNum)) {
                    videoUrl = `${R2_PUBLIC}/melolo/${issue.slug}/ep${String(epNum).padStart(3, '0')}.mp4`;
                } else if (r2.hlsNums.has(epNum)) {
                    videoUrl = `${R2_PUBLIC}/melolo/${issue.slug}/ep${String(epNum).padStart(3, '0')}/playlist.m3u8`;
                } else continue;

                try {
                    await prisma.episode.create({
                        data: {
                            dramaId: issue.id,
                            episodeNumber: epNum,
                            title: `Episode ${epNum}`,
                            videoUrl,
                            duration: 0,
                            isActive: true,
                        },
                    });
                    addedCount++;
                } catch { /* skip duplicates */ }
            }

            // Update totalEpisodes
            const newTotal = existingNums.size + addedCount;
            await prisma.drama.update({
                where: { id: issue.id },
                data: { totalEpisodes: newTotal },
            });

            if (addedCount > 0) {
                console.log(`  ✅ ${issue.title.substring(0, 40)}: +${addedCount} episodes (${existingNums.size} → ${newTotal})`);
                fixed++;
            } else {
                console.log(`  ⏭️  ${issue.title.substring(0, 40)}: no R2 episodes to add`);
            }
        }

        console.log(`\n  Fixed: ${fixed} dramas`);
    } else if (issues.length > 0) {
        console.log(`\n  Run with --fix to register missing R2 episodes to DB.`);
    }

    await prisma.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
