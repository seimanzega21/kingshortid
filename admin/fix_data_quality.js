/**
 * FIX DATA QUALITY — One-pass repair for all DB issues
 * 
 * 1. Broken covers → re-download from vidrama, upload to R2
 * 2. Bad descriptions → pull from metadata.json in R2, or vidrama API
 * 3. Generic genres → infer from title keywords + vidrama API
 * 4. Episode gaps → deactivate dramas with severe gaps
 */
const { PrismaClient } = require('@prisma/client');
const { S3Client, GetObjectCommand, HeadObjectCommand, PutObjectCommand } = require('@aws-sdk/client-s3');
require('dotenv').config();

const p = new PrismaClient();
const R2_PUBLIC = process.env.R2_PUBLIC_URL || 'https://stream.shortlovers.id';
const VIDRAMA_API = 'https://shortdrama.vidrama.com/api/drama';

const s3 = new S3Client({
    region: 'auto',
    endpoint: process.env.R2_ENDPOINT,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
    },
});
const BUCKET = process.env.R2_BUCKET_NAME;

function titleToSlug(title) {
    return title.toLowerCase().replace(/[^a-z0-9\s]/g, '').replace(/\s+/g, '-');
}

// Genre inference from title keywords (Indonesian)
const GENRE_KEYWORDS = {
    'Romantis': ['cinta', 'nikah', 'menikah', 'istri', 'suami', 'manja', 'dimanja', 'romansa', 'kekasih', 'pacar', 'hati', 'mantan', 'pernikahan', 'cerai'],
    'Aksi': ['pertarungan', 'pedang', 'penguasa', 'penakluk', 'senjata', 'lawan', 'perang', 'bangkit'],
    'Drama Keluarga': ['ibu', 'mertua', 'anak', 'keluarga', 'ayah', 'kakak', 'saudara', 'tiri'],
    'Misteri': ['rahasia', 'misteri', 'tersembunyi', 'dusta', 'fitnah'],
    'Komedi': ['lucu', 'hoki', 'beruntung'],
    'Fantasi': ['portal', 'dunia lain', 'dinasti', 'dewi', 'dewa', 'legenda', 'lahir kembali', 'kembali ke', 'bertapa', 'sakti', 'ajaib', 'jiwa'],
    'Balas Dendam': ['balas dendam', 'menyesal', 'penyesalan', 'pengkhianatan'],
    'Bisnis': ['bos', 'ceo', 'kaya', 'harta', 'saham', 'kantor', 'pengacara', 'investor', 'pewaris', 'presdir'],
    'Kehidupan': ['desa', 'kampung', 'petani', 'tabib', 'dokter', 'guru'],
};

function inferGenres(title) {
    const lower = title.toLowerCase();
    const genres = new Set();
    for (const [genre, keywords] of Object.entries(GENRE_KEYWORDS)) {
        for (const kw of keywords) {
            if (lower.includes(kw)) { genres.add(genre); break; }
        }
    }
    if (genres.size === 0) genres.add('Drama');
    return [...genres];
}

async function getR2Metadata(slug) {
    try {
        const r = await s3.send(new GetObjectCommand({ Bucket: BUCKET, Key: `melolo/${slug}/metadata.json` }));
        return JSON.parse(await r.Body.transformToString());
    } catch { return null; }
}

async function checkCoverInR2(slug) {
    try {
        await s3.send(new HeadObjectCommand({ Bucket: BUCKET, Key: `melolo/${slug}/cover.webp` }));
        return true;
    } catch { return false; }
}

async function searchVidrama(title) {
    try {
        const r = await fetch(`${VIDRAMA_API}?action=search&q=${encodeURIComponent(title)}`, {
            signal: AbortSignal.timeout(10000),
        });
        if (!r.ok) return null;
        const data = await r.json();
        const results = data.data?.list || data.data || [];
        // Find best match
        for (const d of results) {
            if (d.title && d.title.toLowerCase() === title.toLowerCase()) return d;
        }
        return results[0] || null;
    } catch { return null; }
}

async function getVidramaDetail(vidramaId) {
    try {
        const r = await fetch(`${VIDRAMA_API}?action=detail&id=${vidramaId}`, {
            signal: AbortSignal.timeout(10000),
        });
        if (!r.ok) return null;
        const data = await r.json();
        return data.data || null;
    } catch { return null; }
}

async function uploadCoverFromUrl(url, slug) {
    try {
        const r = await fetch(url, { signal: AbortSignal.timeout(15000) });
        if (!r.ok) return false;
        const buffer = Buffer.from(await r.arrayBuffer());
        const contentType = r.headers.get('content-type') || 'image/webp';
        await s3.send(new PutObjectCommand({
            Bucket: BUCKET,
            Key: `melolo/${slug}/cover.webp`,
            Body: buffer,
            ContentType: contentType,
        }));
        return true;
    } catch { return false; }
}

async function main() {
    const dramas = await p.drama.findMany({
        where: { isActive: true },
        select: { id: true, title: true, cover: true, description: true, genres: true, totalEpisodes: true },
        orderBy: { title: 'asc' },
    });
    console.log(`\n🔧 Fixing ${dramas.length} dramas...\n`);

    let fixedCover = 0, fixedDesc = 0, fixedGenre = 0, deactivated = 0;
    let coverFailed = 0;

    for (let i = 0; i < dramas.length; i++) {
        const d = dramas[i];
        const slug = titleToSlug(d.title);
        const updates = {};
        const fixes = [];

        // ─── CHECK COVER ─────────────────────────────
        let coverOk = false;
        if (d.cover) {
            try {
                const r = await fetch(d.cover, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
                coverOk = r.ok;
            } catch { }
        }

        if (!coverOk) {
            // Try to find cover in R2
            const hasR2Cover = await checkCoverInR2(slug);
            if (hasR2Cover) {
                updates.cover = `${R2_PUBLIC}/melolo/${slug}/cover.webp`;
                fixes.push('cover_url');
            } else {
                // Search vidrama for cover
                const vidrama = await searchVidrama(d.title);
                if (vidrama) {
                    const urls = [vidrama.originalImage, vidrama.originalPoster, vidrama.poster, vidrama.image].filter(Boolean);
                    let uploaded = false;
                    for (const url of urls) {
                        if (await uploadCoverFromUrl(url, slug)) {
                            updates.cover = `${R2_PUBLIC}/melolo/${slug}/cover.webp`;
                            fixes.push('cover_reupload');
                            uploaded = true;
                            break;
                        }
                    }
                    if (!uploaded) coverFailed++;
                } else {
                    coverFailed++;
                }
            }
        }

        // ─── CHECK DESCRIPTION ───────────────────────
        const isBadDesc = !d.description || d.description === d.title || d.description.length < 10;
        if (isBadDesc) {
            const meta = await getR2Metadata(slug);
            if (meta && meta.description && meta.description.length >= 10 && meta.description !== d.title) {
                updates.description = meta.description;
                fixes.push('desc_from_meta');
            } else {
                // Try vidrama API
                const vidrama = await searchVidrama(d.title);
                if (vidrama) {
                    const desc = vidrama.description || vidrama.desc || '';
                    if (desc.length >= 10) {
                        updates.description = desc;
                        fixes.push('desc_from_api');
                    }
                }
            }
        }

        // ─── CHECK GENRES ────────────────────────────
        const isGeneric = !d.genres || d.genres.length === 0 || (d.genres.length === 1 && d.genres[0] === 'Drama');
        if (isGeneric) {
            // Try metadata first
            const meta = await getR2Metadata(slug);
            if (meta && meta.genres && meta.genres.length > 0) {
                updates.genres = meta.genres;
                fixes.push('genre_from_meta');
            } else {
                // Infer from title
                const inferred = inferGenres(d.title);
                if (inferred.length > 0 && !(inferred.length === 1 && inferred[0] === 'Drama')) {
                    updates.genres = inferred;
                    fixes.push('genre_inferred');
                }
            }
        }

        // ─── CHECK EPISODES ─────────────────────────
        const eps = await p.episode.findMany({
            where: { dramaId: d.id },
            select: { episodeNumber: true },
            orderBy: { episodeNumber: 'asc' },
        });

        if (eps.length > 0) {
            // Check for missing ep1
            if (eps[0].episodeNumber !== 1) {
                // Deactivate — can't play without ep1
                updates.isActive = false;
                fixes.push('DEACTIVATED_no_ep1');
                deactivated++;
            }

            // Check gaps
            let gapCount = 0;
            for (let j = 1; j < eps.length; j++) {
                if (eps[j].episodeNumber !== eps[j - 1].episodeNumber + 1) gapCount++;
            }
            if (gapCount > eps.length * 0.1 && gapCount > 3) {
                updates.isActive = false;
                fixes.push('DEACTIVATED_too_many_gaps');
                deactivated++;
            }
        }

        // ─── APPLY UPDATES ──────────────────────────
        if (Object.keys(updates).length > 0) {
            await p.drama.update({ where: { id: d.id }, data: updates });
            if (fixes.includes('cover_url') || fixes.includes('cover_reupload')) fixedCover++;
            if (fixes.includes('desc_from_meta') || fixes.includes('desc_from_api')) fixedDesc++;
            if (fixes.includes('genre_from_meta') || fixes.includes('genre_inferred')) fixedGenre++;
            console.log(`  ✅ ${d.title}: ${fixes.join(', ')}`);
        }
    }

    console.log(`\n📊 Fix Summary:`);
    console.log(`  🖼️  Covers fixed: ${fixedCover} (${coverFailed} unfixable)`);
    console.log(`  📝 Descriptions fixed: ${fixedDesc}`);
    console.log(`  🏷️  Genres fixed: ${fixedGenre}`);
    console.log(`  🚫 Deactivated (bad episodes): ${deactivated}`);

    const active = await p.drama.count({ where: { isActive: true } });
    console.log(`\n  Active dramas remaining: ${active}`);
    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
