/**
 * fix_genres_v2.js
 * Backfills genres for ALL dramas with empty genres[] in database.
 * Infers genres from title + description using Indonesian keywords.
 * Matches the category list as input by admin.
 *
 * Run: node fix_genres_v2.js
 */

const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

// Genre inference — matches admin-defined categories
function inferGenres(title, description) {
    const text = (title + ' ' + (description || '')).toLowerCase();
    const genres = new Set();

    // Always add Drama as base genre
    genres.add('Drama');

    // 💕 Romantis
    const romanceWords = [
        'cinta', 'nikah', 'suami', 'istri', 'pernikahan', 'romansa', 'menikah',
        'pacaran', 'pacar', 'kekasih', 'jodoh', 'tunangan', 'dicintai', 'mencintai',
        'gadis', 'putri', 'sultan', 'cantik', 'ganteng', 'tampan', 'jatuh cinta',
        'bersama', 'kasih', 'sayang', 'hati', 'pasangan', 'bodyguard', 'pujaan',
    ];
    if (romanceWords.some(w => text.includes(w))) genres.add('Romantis');

    // ⚔️ Aksi
    const actionWords = [
        'bertarung', 'pertarungan', 'tempur', 'battle', 'melawan', 'musuh',
        'perang', 'pasukan', 'senjata', 'duel', 'serang', 'misi', 'operasi',
        'ninja', 'fighter', 'gladiator', 'jagoan',
    ];
    if (actionWords.some(w => text.includes(w))) genres.add('Aksi');

    // ⚡ Sakti (Martial Arts / Cultivation)
    const saktiWords = [
        'sakti', 'kungfu', 'silat', 'pendekar', 'guru', 'ahli', 'master',
        'naga', 'bangkit', 'kekuatan', 'petarung', 'ilmu', 'kanuragan',
        'tinju', 'jurus', 'wushu', 'muay thai',
    ];
    if (saktiWords.some(w => text.includes(w))) genres.add('Sakti');

    // ✨ Fantasi / Sistem
    const fantasyWords = [
        'ajaib', 'sihir', 'portal', 'dunia lain', 'dewa', 'roh', 'supernatural',
        'lahir kembali', 'reinkarnasi', 'sistem', 'dimensi', 'alam lain', 'magis',
        'level', 'exp', 'skill', 'quest', 'panel ajaib', 'giok', 'kiamat',
    ];
    if (fantasyWords.some(w => text.includes(w))) genres.add('Fantasi');
    if (['sistem', 'level', 'exp', 'skill', 'quest', 'panel'].some(w => text.includes(w))) genres.add('Sistem');

    // 💼 CEO / Bisnis
    const bizWords = [
        'ceo', 'bisnis', 'saham', 'perusahaan', 'konglomerat', 'direktur',
        'bos', 'taipan', 'korporat', 'investasi', 'modal', 'presiden direktur',
        'pengusaha', 'direktur utama', 'kantor',
    ];
    if (bizWords.some(w => text.includes(w))) {
        genres.add('Bisnis');
        if (['ceo', 'direktur', 'konglomerat', 'presiden direktur'].some(w => text.includes(w))) genres.add('CEO');
    }

    // 🔫 Mafia / Kriminal
    const mafiaWords = [
        'mafia', 'sindikat', 'kriminal', 'gang', 'bawah tanah', 'narkoba',
        'bandar', 'kejahatan', 'gelap', 'geng', 'preman', 'klan',
    ];
    if (mafiaWords.some(w => text.includes(w))) genres.add('Mafia');

    // 👸 Wanita Kuat
    const wanitaKuatWords = [
        'wanita kuat', 'perempuan tangguh', 'wanita berdaya', 'ibu tunggal',
        'janda', 'gadis berdaya', 'ratu', 'wanita mandiri', 'perempuan hebat',
    ];
    if (wanitaKuatWords.some(w => text.includes(w))) genres.add('Wanita Kuat');

    // ⚔️ Dewa Perang / Militer
    const militerWords = [
        'jenderal', 'panglima', 'militer', 'tentara', 'prajurit', 'barak',
        'pasukan', 'komandan', 'kolonel', 'mayor', 'kapten', 'angkatan',
        'dewa perang', 'perang besar', 'medan tempur',
    ];
    if (militerWords.some(w => text.includes(w))) genres.add('Dewa Perang');

    // 🔥 Balas Dendam
    const dendamWords = [
        'balas dendam', 'dendam', 'membalas', 'revenge', 'keadilan',
        'amarah', 'membalas sakit hati', 'menuntut balas', 'fitnah',
        'pengkhianatan', 'pengkhianat', 'dikhianati', 'dijebak', 'dibuang',
    ];
    if (dendamWords.some(w => text.includes(w))) genres.add('Balas Dendam');

    // 👑 Pewaris
    const pewariWords = [
        'pewaris', 'warisan', 'ahli waris', 'mewarisi', 'keturunan',
        'harta pusaka', 'waris', 'mahkota',
    ];
    if (pewariWords.some(w => text.includes(w))) genres.add('Pewaris');

    // 👨‍👩‍👧 Keluarga
    const familyWords = [
        'keluarga', 'anak', 'ibu', 'ayah', 'adik', 'kakak',
        'orang tua', 'rumah tangga', 'saudara', 'orangtua',
    ];
    if (familyWords.some(w => text.includes(w))) genres.add('Keluarga');

    // 🔍 Misteri
    const mysteryWords = [
        'misteri', 'rahasia', 'pembunuh', 'detektif', 'tersembunyi',
        'terjebak', 'jebakan', 'teka-teki', 'investigasi', 'kasus',
    ];
    if (mysteryWords.some(w => text.includes(w))) genres.add('Misteri');

    // 🎙️ Sulih Suara (Indonesian dub marker)
    const sulihWords = ['sulih suara', 'dubbing', 'alih bahasa'];
    if (sulihWords.some(w => text.includes(w))) genres.add('Sulih Suara');

    return Array.from(genres);
}

async function main() {
    // Get ALL active dramas (re-classify even those with only ['Drama'])
    const all = await p.drama.findMany({
        where: { isActive: true },
        select: { id: true, title: true, description: true, genres: true },
    });

    const toUpdate = all.filter(d =>
        !d.genres || d.genres.length === 0 ||
        (d.genres.length === 1 && d.genres[0] === 'Drama') // only generic Drama
    );
    const skip = all.length - toUpdate.length;
    console.log(`\n=== GENRE BACKFILL ===`);
    console.log(`Total dramas: ${all.length}`);
    console.log(`To update (empty or only 'Drama'): ${toUpdate.length}`);
    console.log(`Already classified (skip): ${skip}\n`);

    // 2. Infer and update
    let updated = 0;
    for (const d of toUpdate) {
        const genres = inferGenres(d.title, d.description || '');
        await p.drama.update({
            where: { id: d.id },
            data: { genres },
        });
        console.log(`✅ ${d.title}`);
        console.log(`   → ${genres.join(', ')}\n`);
        updated++;
    }

    console.log(`\n✅ Done! Updated ${updated}/${toUpdate.length} dramas.`);

    // 3. Final stats
    const genreCounts = {};
    const afterAll = await p.drama.findMany({ where: { isActive: true }, select: { genres: true } });
    for (const d of afterAll) {
        for (const g of (d.genres || [])) {
            genreCounts[g] = (genreCounts[g] || 0) + 1;
        }
    }
    console.log('\n=== GENRE DISTRIBUTION ===');
    Object.entries(genreCounts)
        .sort((a, b) => b[1] - a[1])
        .forEach(([g, c]) => console.log(`  ${g}: ${c} dramas`));

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
