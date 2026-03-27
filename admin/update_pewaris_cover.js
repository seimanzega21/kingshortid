/**
 * Download cover from mydramawave and upload to R2
 * Then update the database
 */
const { PrismaClient } = require('@prisma/client');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const https = require('https');
const http = require('http');
require('dotenv').config();

const prisma = new PrismaClient();
const R2_PUBLIC = 'https://stream.shortlovers.id';
const DRAMA_ID = '10d364be-e338-45cb-a5be-53619294d595';

const s3 = new S3Client({
    region: 'auto',
    endpoint: process.env.R2_ENDPOINT,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
    },
});
const BUCKET = process.env.R2_BUCKET_NAME;

function downloadBuffer(url) {
    return new Promise((resolve, reject) => {
        const client = url.startsWith('https') ? https : http;
        const req = client.get(url, { 
            timeout: 30000,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://mydramawave.com/',
            }
        }, res => {
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                return downloadBuffer(res.headers.location).then(resolve).catch(reject);
            }
            if (res.statusCode !== 200) return reject(new Error(`HTTP ${res.statusCode} for ${url}`));
            const chunks = [];
            res.on('data', c => chunks.push(c));
            res.on('end', () => resolve(Buffer.concat(chunks)));
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    });
}

async function tryDownload(urls) {
    for (const url of urls) {
        try {
            console.log(`  Trying: ${url}`);
            const buf = await downloadBuffer(url);
            if (buf.length > 1000) {
                console.log(`  ✅ Downloaded ${(buf.length / 1024).toFixed(0)}KB`);
                return { buf, url };
            }
            console.log(`  ⚠️ Too small: ${buf.length} bytes`);
        } catch (e) {
            console.log(`  ❌ Failed: ${e.message}`);
        }
    }
    return null;
}

async function main() {
    console.log('=== Cover Update Script ===\n');
    
    // Get current drama info
    const drama = await prisma.drama.findUnique({
        where: { id: DRAMA_ID },
        select: { id: true, title: true, cover: true, isActive: true }
    });
    
    if (!drama) {
        console.log('Drama not found!');
        return;
    }
    
    console.log(`Drama: ${drama.title}`);
    console.log(`Current cover: ${drama.cover || '(none)'}`);
    console.log(`Active: ${drama.isActive}\n`);
    
    // Try multiple sources for the cover
    // The mydramawave series ID from the URL: w5FPPf5qIJ
    const coverUrls = [
        // Try mydramawave API / static assets for series w5FPPf5qIJ
        'https://static-v1.mydramawave.com/poster/w5FPPf5qIJ.webp',
        'https://static-v1.mydramawave.com/poster/w5FPPf5qIJ.jpg',
        'https://static-v1.mydramawave.com/cover/w5FPPf5qIJ.webp',
        'https://static-v1.mydramawave.com/cover/w5FPPf5qIJ.jpg',
        'https://static-v1.mydramawave.com/image/w5FPPf5qIJ.webp',
        'https://static-v1.mydramawave.com/image/w5FPPf5qIJ.jpg',
        // Try video-v6 patterns (same domain as video content)
        'https://video-v6.mydramawave.com/poster/w5FPPf5qIJ.webp',
        'https://video-v6.mydramawave.com/poster/w5FPPf5qIJ.jpg',
        // Try the freereels pattern that other dramas use
        'https://freereels.app/api/drama/cover/pewaris-asli-kembali-untuk-bal',
        // Try static patterns with different structures
        'https://mydramawave.com/api/series/w5FPPf5qIJ/cover',
        'https://api.mydramawave.com/series/w5FPPf5qIJ/poster',
    ];
    
    console.log('Attempting to download cover...\n');
    const result = await tryDownload(coverUrls);
    
    if (result) {
        const { buf, url } = result;
        let ext = 'jpg';
        if (url.includes('.webp')) ext = 'webp';
        else if (url.includes('.png')) ext = 'png';
        
        const slug = 'freereels/pewaris_asli_kembali_untuk_bal';
        const newKey = `${slug}/cover.${ext}`;
        const ct = ext === 'webp' ? 'image/webp' : ext === 'png' ? 'image/png' : 'image/jpeg';
        
        console.log(`\nUploading to R2: ${newKey}`);
        await s3.send(new PutObjectCommand({
            Bucket: BUCKET, Key: newKey, Body: buf, ContentType: ct,
        }));
        
        const newUrl = `${R2_PUBLIC}/${newKey}`;
        await prisma.drama.update({ 
            where: { id: DRAMA_ID }, 
            data: { cover: newUrl }
        });
        
        console.log(`\n✅ Cover updated to: ${newUrl}`);
    } else {
        console.log('\n❌ Could not download cover from any source.');
        console.log('You may need to manually upload the cover via the admin panel.');
    }
    
    await prisma.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
