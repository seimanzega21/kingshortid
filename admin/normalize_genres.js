/**
 * normalize_genres.js
 * Maps existing non-standard genre names to admin-defined categories.
 * Run AFTER fix_genres_v2.js
 *
 * Run: node normalize_genres.js
 */
const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

// Maps any variant → official admin category name
const GENRE_MAP = {
    // Romantis
    'Romantis': 'Romantis', 'Romansa': 'Romantis', 'Romance': 'Romantis',
    'Romastis': 'Romantis', 'Periode Romantis': 'Romantis',
    'Action Romance': 'Romantis', 'Romansa Urban': 'Romantis',
    'Cinta yang pahit': 'Romantis', 'Cinta Satu Malam': 'Romantis',
    'Perbedaan usia': 'Romantis',

    // Aksi
    'Aksi': 'Aksi', 'Action': 'Aksi', 'Action Romance': 'Aksi',
    'Tak terkalahkan': 'Aksi', 'Kekuatan super': 'Aksi',

    // Sakti
    'Sakti': 'Sakti', 'Imajinasi Pria': 'Sakti',

    // Fantasi
    'Fantasi': 'Fantasi', 'Fantasi perkotaan': 'Fantasi',
    'Kelahiran kembali': 'Fantasi', 'Kembali': 'Fantasi',
    'Time Travel': 'Fantasi', 'Sci-Fi': 'Fantasi',
    'Imajinasi Perkotaan': 'Fantasi', 'Swap Identitas': 'Fantasi',

    // Sistem
    'Sistem': 'Sistem',

    // CEO / Bisnis
    'CEO': 'CEO', 'Ceo': 'CEO',
    'Bisnis': 'Bisnis', 'Tycoon': 'Bisnis',
    'Drama Kantor': 'Bisnis', 'Pertanian Perkotaan': 'Bisnis',

    // Mafia
    'Mafia': 'Mafia', 'Harem': 'Mafia',

    // Wanita Kuat
    'Wanita Kuat': 'Wanita Kuat', 'Pemeran Utama Wanita Kuat': 'Wanita Kuat',
    'Pertumbuhan Wanita': 'Wanita Kuat',

    // Dewa Perang
    'Dewa Perang': 'Dewa Perang', 'Panglima Perang': 'Dewa Perang',

    // Balas Dendam
    'Balas Dendam': 'Balas Dendam', 'Serangan balik': 'Balas Dendam',
    'Pembalasan dendam': 'Balas Dendam', 'Identitas Tersembunyi': 'Balas Dendam',

    // Keluarga
    'Keluarga': 'Keluarga', 'Drama Keluarga': 'Keluarga',

    // Drama
    'Drama': 'Drama', 'Kehidupan': 'Drama', 'Kehidupan perkotaan': 'Drama',
    'Drama Sejarah': 'Drama', 'Bukan siapa-siapa': 'Drama',
    'Desa': 'Drama', 'Duda': 'Drama', 'Pemeran Utama Pria': 'Drama',

    // Pewaris
    'Pewaris': 'Pewaris', 'Menantu Pria': 'Pewaris',

    // Misteri
    'Misteri': 'Misteri',

    // Komedi
    'Komedi': 'Komedi', 'Dokter': 'Komedi',

    // Romansa Urban → Romantis
    'Romansa Urban': 'Romantis',

    // Drop
    'Lainnya': null,
};

function normalizeGenres(genres) {
    const result = new Set();
    for (const g of genres) {
        const mapped = GENRE_MAP[g];
        if (mapped === null) continue; // drop
        if (mapped) result.add(mapped);
        else result.add(g); // keep unknown
    }
    if (result.size === 0) result.add('Drama');
    return Array.from(result);
}

async function main() {
    const all = await p.drama.findMany({
        where: { isActive: true },
        select: { id: true, title: true, genres: true },
    });

    console.log(`\n=== NORMALIZING ${all.length} DRAMAS ===\n`);
    let updated = 0;

    for (const d of all) {
        const original = d.genres || [];
        const normalized = normalizeGenres(original);

        // Only update if changed
        const changed = JSON.stringify(original.slice().sort()) !== JSON.stringify(normalized.slice().sort());
        if (!changed) continue;

        await p.drama.update({ where: { id: d.id }, data: { genres: normalized } });
        updated++;
        if (updated <= 20 || updated % 50 === 0) {
            console.log(`${d.title}: [${original.join(', ')}] → [${normalized.join(', ')}]`);
        }
    }

    console.log(`\nUpdated: ${updated}/${all.length} dramas\n`);

    // Final distribution
    const afterAll = await p.drama.findMany({ where: { isActive: true }, select: { genres: true } });
    const counts = {};
    for (const d of afterAll) {
        for (const g of (d.genres || [])) counts[g] = (counts[g] || 0) + 1;
    }
    console.log('=== FINAL GENRE DISTRIBUTION ===');
    Object.entries(counts).sort((a, b) => b[1] - a[1])
        .forEach(([g, c]) => console.log(`  ${g}: ${c}`));

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
