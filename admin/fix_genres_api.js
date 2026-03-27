/**
 * fix_genres_api.js
 * Fetches all dramas from production API, infers genres from title/description,
 * then PATCHes each drama via the admin API.
 *
 * Run: node fix_genres_api.js
 */
const https = require('https');

const API_BASE = 'https://api.shortlovers.id/api';
const ADMIN_KEY = 'ksh-admin-2026-s3cur3-k3y-x7m9p2';

// Keyword → genre mapping (Indonesian)
const KEYWORD_GENRES = [
    { genre: 'Romantis', keywords: ['cinta', 'nikah', 'kawin', 'menikah', 'suami', 'istri', 'kekasih', 'hubungan', 'romant', 'pasangan', 'jodoh', 'cinderella', 'Valentine'] },
    { genre: 'Balas Dendam', keywords: ['balas dendam', 'dendam', 'pembalasan', 'serangan balik', 'hancurkan', 'membalas', 'kejahatan', 'penjara', 'fitnah', 'pengkhianat'] },
    { genre: 'CEO', keywords: ['CEO', 'direktur', 'bos', 'perusahaan', 'korporat', 'konglomerat', 'taipan', 'pebisnis', 'hartawan'] },
    { genre: 'Bisnis', keywords: ['bisnis', 'usaha', 'dagang', 'industri', 'ekonomi', 'modal', 'investasi', 'saham', 'perusahaan', 'tycoon'] },
    { genre: 'Keluarga', keywords: ['keluarga', 'ayah', 'ibu', 'anak', 'kakak', 'adik', 'saudara', 'orang tua', 'mertua', 'menantu', 'cucu', 'kakek', 'nenek'] },
    { genre: 'Aksi', keywords: ['pertarungan', 'bela diri', 'perang', 'jagoan', 'superhero', 'militer', 'prajurit', 'tentara', 'jenderal', 'pasukan', 'senjata', 'barak'] },
    { genre: 'Dewa Perang', keywords: ['dewa perang', 'panglima', 'jenderal', 'perang', 'pasukan', 'militer', 'barak', 'prajurit', 'tentara', 'komandan'] },
    { genre: 'Pewaris', keywords: ['pewaris', 'warisan', 'mahkota', 'tahta', 'kerajaan', 'menantu', 'marga', 'klan', 'dinasti'] },
    { genre: 'Mafia', keywords: ['mafia', 'gangster', 'bawah tanah', 'sindikat', 'kejahatan terorganisir', 'bos kriminal', 'dunia gelap'] },
    { genre: 'Fantasi', keywords: ['fantasi', 'sihir', 'naga', 'ajaib', 'kekuatan super', 'sistem', 'kembali ke masa', 'kelahiran kembali', 'reinkarnasi', 'transmigrate', 'time travel', 'sci-fi'] },
    { genre: 'Sakti', keywords: ['sakti', 'tak terkalahkan', 'legenda', 'dewa', 'ilmu tinggi', 'kekuatan luar biasa', 'tanpa tanding'] },
    { genre: 'Sistem', keywords: ['sistem', 'level up', 'quest', 'upgrade', 'skill', 'point', 'status bar', 'game system'] },
    { genre: 'Wanita Kuat', keywords: ['wanita kuat', 'perempuan kuat', 'wanita perkasa', 'heroin', 'wanita tangguh', 'perempuan tangguh'] },
    { genre: 'Misteri', keywords: ['misteri', 'teka-teki', 'rahasia', 'tersembunyi', 'investigasi', 'detektif', 'kasus', 'pembunuhan', 'hilang'] },
    { genre: 'Komedi', keywords: ['komedi', 'lucu', 'humor', 'lawak', 'kocak', 'jenaka', 'lelucon'] },
];

function inferGenres(title, description) {
    const text = `${title} ${description}`.toLowerCase();
    const genres = new Set();
    for (const { genre, keywords } of KEYWORD_GENRES) {
        if (keywords.some(k => text.includes(k.toLowerCase()))) {
            genres.add(genre);
        }
    }
    if (genres.size === 0) genres.add('Drama');
    return Array.from(genres);
}

function fetchJson(url, options = {}) {
    return new Promise((resolve, reject) => {
        const req = https.request(url, options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try { resolve(JSON.parse(data)); }
                catch (e) { reject(new Error(`Parse error: ${data.slice(0, 200)}`)); }
            });
        });
        req.on('error', reject);
        if (options.body) req.write(options.body);
        req.end();
    });
}

async function getAllDramas() {
    const first = await fetchJson(`${API_BASE}/dramas?page=1&limit=1`);
    const total = parseInt(first.total);
    const perPage = 50;
    const pages = Math.ceil(total / perPage);
    const all = [];
    console.log(`Fetching ${total} dramas across ${pages} pages...`);
    for (let p = 1; p <= pages; p++) {
        const res = await fetchJson(`${API_BASE}/dramas?page=${p}&limit=${perPage}`);
        all.push(...(res.dramas || []));
        process.stdout.write(`  Page ${p}/${pages}\r`);
    }
    console.log(`\nFetched ${all.length} dramas`);
    return all;
}

async function patchDramaGenre(id, genres) {
    const body = JSON.stringify({ genres });
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'api.shortlovers.id',
            path: `/api/admin/dramas/${id}`,
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(body),
                'X-Admin-Key': ADMIN_KEY,
            },
        };
        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve({ status: res.statusCode, data }));
        });
        req.on('error', reject);
        req.write(body);
        req.end();
    });
}

async function main() {
    const dramas = await getAllDramas();
    const empty = dramas.filter(d => !d.genres || d.genres.length === 0);
    console.log(`\nDramas with empty genres: ${empty.length}`);

    let updated = 0, failed = 0;
    for (const drama of empty) {
        const genres = inferGenres(drama.title || '', drama.description || '');
        const result = await patchDramaGenre(drama.id, genres);
        if (result.status >= 200 && result.status < 300) {
            updated++;
            if (updated <= 10 || updated % 25 === 0) {
                console.log(`✅ ${drama.title} → [${genres.join(', ')}]`);
            }
        } else {
            failed++;
            console.log(`❌ ${drama.title} (${result.status}): ${result.data.slice(0, 100)}`);
        }
        // Small delay to avoid rate limiting
        await new Promise(r => setTimeout(r, 100));
    }

    console.log(`\nDone! Updated: ${updated}, Failed: ${failed}`);
}

main().catch(console.error);
