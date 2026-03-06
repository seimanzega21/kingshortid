/**
 * COVER AUDIT & FIX
 * ==================
 * Checks all drama cover URLs in DB, finds broken ones,
 * tries to find correct cover in R2 or downloads from Vidrama API.
 *
 * Usage:
 *   node fix_covers.js           # Audit only
 *   node fix_covers.js --fix     # Audit + fix broken covers
 */
const { PrismaClient } = require('@prisma/client');
const { S3Client, ListObjectsV2Command, PutObjectCommand } = require('@aws-sdk/client-s3');
const https = require('https');
const http = require('http');
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

function slugify(text) {
    return text.toLowerCase().trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_]+/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function checkUrl(url) {
    return new Promise(resolve => {
        const client = url.startsWith('https') ? https : http;
        const req = client.request(url, { method: 'HEAD', timeout: 10000 }, res => {
            resolve({ status: res.statusCode, ok: res.statusCode >= 200 && res.statusCode < 400 });
        });
        req.on('error', () => resolve({ status: 0, ok: false }));
        req.on('timeout', () => { req.destroy(); resolve({ status: 0, ok: false }); });
        req.end();
    });
}

function downloadBuffer(url) {
    return new Promise((resolve, reject) => {
        const client = url.startsWith('https') ? https : http;
        client.get(url, { timeout: 15000 }, res => {
            if (res.statusCode !== 200) return reject(new Error(`HTTP ${res.statusCode}`));
            const chunks = [];
            res.on('data', c => chunks.push(c));
            res.on('end', () => resolve(Buffer.concat(chunks)));
        }).on('error', reject);
    });
}

function fetchJSON(url) {
    return new Promise((resolve, reject) => {
        https.get(url, { timeout: 15000 }, res => {
            let data = '';
            res.on('data', c => data += c);
            res.on('end', () => {
                try { resolve(JSON.parse(data)); }
                catch (e) { reject(e); }
            });
        }).on('error', reject);
    });
}

async function findR2Cover(slug) {
    // Check various cover file extensions in R2
    const extensions = ['webp', 'jpg', 'jpeg', 'png'];
    const cmd = new ListObjectsV2Command({
        Bucket: BUCKET,
        Prefix: `melolo/${slug}/cover`,
    });
    try {
        const resp = await s3.send(cmd);
        const coverFiles = (resp.Contents || []).map(o => o.Key);
        if (coverFiles.length > 0) {
            return `${R2_PUBLIC}/${coverFiles[0]}`;
        }
    } catch { }
    return null;
}

async function downloadAndUploadCover(slug, sourceUrl) {
    try {
        const buffer = await downloadBuffer(sourceUrl);
        if (buffer.length < 1000) return null;

        // Determine extension from source URL
        let ext = 'webp';
        if (sourceUrl.includes('.jpg') || sourceUrl.includes('.jpeg')) ext = 'jpg';
        else if (sourceUrl.includes('.png')) ext = 'png';

        const r2Key = `melolo/${slug}/cover.${ext}`;
        const contentType = ext === 'jpg' ? 'image/jpeg' : ext === 'png' ? 'image/png' : 'image/webp';

        await s3.send(new PutObjectCommand({
            Bucket: BUCKET,
            Key: r2Key,
            Body: buffer,
            ContentType: contentType,
        }));

        return `${R2_PUBLIC}/${r2Key}`;
    } catch (e) {
        return null;
    }
}

async function getVidramaCover(title) {
    try {
        const searchUrl = `${VIDRAMA_API}?action=search&keyword=${encodeURIComponent(title)}&limit=5`;
        const data = await fetchJSON(searchUrl);
        const items = data.data || [];
        const titleLower = title.toLowerCase();

        let match = items.find(x => x.title.toLowerCase() === titleLower);
        if (!match) match = items.find(x =>
            x.title.toLowerCase().includes(titleLower) || titleLower.includes(x.title.toLowerCase())
        );
        if (!match && items.length > 0) match = items[0];

        if (match && match.cover) return match.cover;
    } catch { }
    return null;
}

async function main() {
    const doFix = process.argv.includes('--fix');

    console.log('='.repeat(65));
    console.log('  COVER AUDIT & FIX');
    console.log(`  Mode: ${doFix ? '🔧 FIX' : '🔍 AUDIT'}`);
    console.log('='.repeat(65));

    const dramas = await prisma.drama.findMany({
        select: { id: true, title: true, cover: true },
        where: { isActive: true },
        orderBy: { title: 'asc' },
    });
    console.log(`\n  Checking ${dramas.length} drama covers...\n`);

    const broken = [];
    let ok = 0;

    for (let i = 0; i < dramas.length; i++) {
        const d = dramas[i];
        const result = await checkUrl(d.cover);

        if (!result.ok) {
            broken.push({ ...d, httpStatus: result.status });
            process.stdout.write(`  ${String(i + 1).padStart(3)}. ❌ ${d.title.substring(0, 45).padEnd(45)} ${d.cover.split('/').pop()} (${result.status})\n`);
        } else {
            ok++;
        }

        // Rate limit
        if (i % 10 === 0) await sleep(100);
    }

    console.log(`\n${'='.repeat(65)}`);
    console.log(`  RESULTS`);
    console.log(`${'='.repeat(65)}`);
    console.log(`  Total checked: ${dramas.length}`);
    console.log(`  OK: ${ok}`);
    console.log(`  Broken: ${broken.length}`);

    if (broken.length === 0) {
        console.log('\n  All covers are working! 🎉');
        await prisma.$disconnect();
        return;
    }

    if (!doFix) {
        console.log(`\n  Run with --fix to attempt automatic repair.`);
        await prisma.$disconnect();
        return;
    }

    // Fix broken covers
    console.log(`\n${'='.repeat(65)}`);
    console.log(`  FIXING BROKEN COVERS...`);
    console.log(`${'='.repeat(65)}`);

    let fixed = 0, unfixed = 0;

    for (const d of broken) {
        const slug = slugify(d.title);
        let newUrl = null;

        // Strategy 1: Look for cover in R2 with different extension
        newUrl = await findR2Cover(slug);
        if (newUrl && newUrl !== d.cover) {
            const check = await checkUrl(newUrl);
            if (check.ok) {
                await prisma.drama.update({ where: { id: d.id }, data: { cover: newUrl } });
                console.log(`  ✅ ${d.title.substring(0, 40)} — found in R2: ${newUrl.split('/').pop()}`);
                fixed++;
                continue;
            }
        }

        // Strategy 2: Download from Vidrama API
        const vidramaCoverUrl = await getVidramaCover(d.title);
        await sleep(300);

        if (vidramaCoverUrl) {
            const uploadedUrl = await downloadAndUploadCover(slug, vidramaCoverUrl);
            if (uploadedUrl) {
                await prisma.drama.update({ where: { id: d.id }, data: { cover: uploadedUrl } });
                console.log(`  ✅ ${d.title.substring(0, 40)} — downloaded from Vidrama API`);
                fixed++;
                continue;
            }
        }

        // Strategy 3: Try common cover filenames in R2
        const tryUrls = [
            `${R2_PUBLIC}/melolo/${slug}/cover.webp`,
            `${R2_PUBLIC}/melolo/${slug}/cover.jpg`,
            `${R2_PUBLIC}/melolo/${slug}/cover.png`,
        ];

        let found = false;
        for (const tryUrl of tryUrls) {
            if (tryUrl === d.cover) continue;
            const check = await checkUrl(tryUrl);
            if (check.ok) {
                await prisma.drama.update({ where: { id: d.id }, data: { cover: tryUrl } });
                console.log(`  ✅ ${d.title.substring(0, 40)} — found at: ${tryUrl.split('/').pop()}`);
                fixed++;
                found = true;
                break;
            }
        }

        if (!found) {
            console.log(`  ❌ ${d.title.substring(0, 40)} — no cover found anywhere`);
            unfixed++;
        }
    }

    console.log(`\n${'='.repeat(65)}`);
    console.log(`  Fixed: ${fixed}`);
    console.log(`  Still broken: ${unfixed}`);
    console.log(`${'='.repeat(65)}`);

    await prisma.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
