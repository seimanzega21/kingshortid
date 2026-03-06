const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

// Genre inference based on title/description keywords
function inferGenres(title, description) {
    const text = (title + ' ' + (description || '')).toLowerCase();
    const genres = new Set();

    // Always add Drama as base genre
    genres.add('Drama');

    // Romance indicators
    const romanceWords = ['cinta', 'nikah', 'suami', 'istri', 'pernikahan', 'romansa',
        'pacaran', 'pacar', 'kekasih', 'hati', 'jodoh', 'menikah', 'tunangan',
        'dicintai', 'mencintai', 'cintai', 'kucintai', 'digoda', 'gadis', 'putri',
        'menaklukkan', 'dimanja', 'bodyguard', 'pengacara', 'dosen', 'idola',
        'sahabat', 'bersinar', 'sultan', 'cantik', 'ganteng', 'tampan'];
    if (romanceWords.some(w => text.includes(w))) genres.add('Romantis');

    // Comedy
    const comedyWords = ['lucu', 'kocak', 'komedi', 'humor', 'galak', 'konyol', 'manja'];
    if (comedyWords.some(w => text.includes(w))) genres.add('Komedi');

    // Action/Martial arts
    const actionWords = ['sakti', 'petarung', 'naga', 'kungfu', 'pertarungan',
        'bangkit', 'kekuatan', 'maut', 'bertarung', 'ahli', 'master'];
    if (actionWords.some(w => text.includes(w))) genres.add('Aksi');

    // Fantasy/Supernatural
    const fantasyWords = ['ajaib', 'sihir', 'portal', 'dunia lain', 'dewa', 'giok',
        'kiamat', 'lahir kembali', 'sistem', 'reinkarnasi', 'supernatural', 'roh'];
    if (fantasyWords.some(w => text.includes(w))) genres.add('Fantasi');

    // Business/CEO/Rich
    const bizWords = ['ceo', 'bisnis', 'saham', 'kaya', 'miskin', 'perusahaan',
        'konglomerat', 'direktur', 'bos', 'mafia', 'taipan'];
    if (bizWords.some(w => text.includes(w))) genres.add('Bisnis');

    // Mystery/Thriller
    const mysteryWords = ['rahasia', 'misteri', 'pembunuh', 'detektif', 'jebakan',
        'tersembunyi', 'lensa', 'terjebak'];
    if (mysteryWords.some(w => text.includes(w))) genres.add('Misteri');

    // Family
    const familyWords = ['keluarga', 'anak', 'ibu', 'ayah', 'adik', 'kakak',
        'orang tua', 'rumah tangga'];
    if (familyWords.some(w => text.includes(w))) genres.add('Keluarga');

    return Array.from(genres);
}

async function main() {
    const dramas = await p.drama.findMany({
        where: { isActive: true, genres: { isEmpty: true } }
    });

    console.log(`Found ${dramas.length} dramas with empty genres\n`);

    for (const d of dramas) {
        const genres = inferGenres(d.title, d.description);
        await p.drama.update({
            where: { id: d.id },
            data: { genres }
        });
        console.log(`${d.title}`);
        console.log(`  → ${genres.join(', ')}\n`);
    }

    console.log(`\nDone! Updated ${dramas.length} dramas.`);
    await p.$disconnect();
}
main().catch(e => { console.error(e); process.exit(1); });
