/**
 * COVER FIX v2 — Deep search with Vidrama detail API
 * ====================================================
 * Gets broken covers, searches Vidrama detail API for cover URL,
 * downloads and uploads to R2, updates DB.
 */
const { PrismaClient } = require('@prisma/client');
const { S3Client, PutObjectCommand, ListObjectsV2Command } = require('@aws-sdk/client-s3');
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
            resolve(res.statusCode >= 200 && res.statusCode < 400);
        });
        req.on('error', () => resolve(false));
        req.on('timeout', () => { req.destroy(); resolve(false); });
        req.end();
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

function downloadBuffer(url) {
    return new Promise((resolve, reject) => {
        const client = url.startsWith('https') ? https : http;
        const req = client.get(url, { timeout: 15000 }, res => {
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                // Follow redirect
                return downloadBuffer(res.headers.location).then(resolve).catch(reject);
            }
            if (res.statusCode !== 200) return reject(new Error(`HTTP ${res.statusCode}`));
            const chunks = [];
            res.on('data', c => chunks.push(c));
            res.on('end', () => resolve(Buffer.concat(chunks)));
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    });
}

async function findR2CoverKey(slug) {
    try {
        const cmd = new ListObjectsV2Command({ Bucket: BUCKET, Prefix: `melolo/${slug}/cover` });
        const resp = await s3.send(cmd);
        const files = (resp.Contents || []).filter(o =>
            o.Key.match(/cover\.(webp|jpg|jpeg|png)$/i) && o.Size > 1000
        );
        if (files.length > 0) return files[0].Key;
    } catch { }

    // Also check for poster files
    try {
        const cmd = new ListObjectsV2Command({ Bucket: BUCKET, Prefix: `melolo/${slug}/poster` });
        const resp = await s3.send(cmd);
        const files = (resp.Contents || []).filter(o =>
            o.Key.match(/poster\.(webp|jpg|jpeg|png)$/i) && o.Size > 1000
        );
        if (files.length > 0) return files[0].Key;
    } catch { }

    return null;
}

async function main() {
    console.log('='.repeat(65));
    console.log('  COVER FIX v2 — Deep Vidrama Search');
    console.log('='.repeat(65));

    const dramas = await prisma.drama.findMany({
        select: { id: true, title: true, cover: true },
        where: { isActive: true },
        orderBy: { title: 'asc' },
    });

    // Find broken covers
    console.log(`\n  Checking ${dramas.length} covers...`);
    const broken = [];
    for (const d of dramas) {
        const ok = await checkUrl(d.cover);
        if (!ok) broken.push(d);
    }
    console.log(`  Broken: ${broken.length} / ${dramas.length}\n`);

    if (broken.length === 0) {
        console.log('  All covers OK! 🎉');
        await prisma.$disconnect();
        return;
    }

    let fixed = 0, notfound = 0;

    for (let i = 0; i < broken.length; i++) {
        const d = broken[i];
        const slug = slugify(d.title);
        const num = `[${i + 1}/${broken.length}]`;

        // Strategy 1: Check R2 for existing cover/poster with any extension
        const r2Key = await findR2CoverKey(slug);
        if (r2Key) {
            const r2Url = `${R2_PUBLIC}/${r2Key}`;
            const ok = await checkUrl(r2Url);
            if (ok) {
                await prisma.drama.update({ where: { id: d.id }, data: { cover: r2Url } });
                console.log(`  ${num} ✅ ${d.title.substring(0, 40)} — R2: ${r2Key.split('/').pop()}`);
                fixed++;
                continue;
            }
        }

        // Strategy 2: Search Vidrama and get cover from detail API
        try {
            const searchData = await fetchJSON(
                `${VIDRAMA_API}?action=search&keyword=${encodeURIComponent(d.title)}&limit=10`
            );
            await sleep(300);
            const items = searchData.data || [];
            const titleLower = d.title.toLowerCase();
            let match = items.find(x => x.title && x.title.toLowerCase() === titleLower);
            if (!match) match = items.find(x => x.title && (
                x.title.toLowerCase().includes(titleLower) || titleLower.includes(x.title.toLowerCase())
            ));
            if (!match && items.length > 0) match = items[0];

            if (match) {
                // Get detail for cover
                const detailData = await fetchJSON(`${VIDRAMA_API}?action=detail&id=${match.id}`);
                await sleep(300);
                const detail = detailData.data || {};

                // Try multiple cover sources
                const coverUrls = [
                    detail.cover, detail.poster, detail.thumbnail,
                    match.cover, match.poster, match.thumbnail,
                ].filter(Boolean);

                let uploaded = false;
                for (const coverUrl of coverUrls) {
                    try {
                        const buf = await downloadBuffer(coverUrl);
                        if (buf.length < 1000) continue;

                        let ext = 'jpg';
                        if (coverUrl.includes('.webp')) ext = 'webp';
                        else if (coverUrl.includes('.png')) ext = 'png';

                        const newKey = `melolo/${slug}/cover.${ext}`;
                        const ct = ext === 'webp' ? 'image/webp' : ext === 'png' ? 'image/png' : 'image/jpeg';

                        await s3.send(new PutObjectCommand({
                            Bucket: BUCKET, Key: newKey, Body: buf, ContentType: ct,
                        }));

                        const newUrl = `${R2_PUBLIC}/${newKey}`;
                        await prisma.drama.update({ where: { id: d.id }, data: { cover: newUrl } });
                        console.log(`  ${num} ✅ ${d.title.substring(0, 40)} — downloaded from Vidrama (${(buf.length / 1024).toFixed(0)}KB)`);
                        fixed++;
                        uploaded = true;
                        break;
                    } catch { }
                }

                if (uploaded) continue;
            }
        } catch { }

        console.log(`  ${num} ❌ ${d.title.substring(0, 40)} — no cover source found`);
        notfound++;
    }

    console.log(`\n${'='.repeat(65)}`);
    console.log(`  Fixed: ${fixed}`);
    console.log(`  Still broken: ${notfound}`);
    console.log('='.repeat(65));

    await prisma.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
