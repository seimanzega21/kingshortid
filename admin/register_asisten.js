// Register the 35 missing episodes for "Asisten yang Ternyata Istri Bos" into DB
const { PrismaClient } = require('@prisma/client');
require('dotenv').config();
const p = new PrismaClient();
const R2_PUBLIC = 'https://stream.shortlovers.id';
const SLUG = 'asisten-yang-ternyata-istri-bos';

async function main() {
    const drama = await p.drama.findFirst({ where: { title: { contains: 'Asisten yang Ternyata' } } });
    if (!drama) { console.log('NOT FOUND'); return; }

    console.log('Drama:', drama.title, '(ID:', drama.id + ')');

    // Get existing episodes
    const existing = await p.episode.findMany({
        where: { dramaId: drama.id },
        select: { episodeNumber: true },
    });
    const existingNums = new Set(existing.map(e => e.episodeNumber));
    console.log('Existing episodes:', existingNums.size);

    // Register missing ep3-37
    let added = 0;
    for (let ep = 3; ep <= 37; ep++) {
        if (existingNums.has(ep)) {
            console.log('  ep' + ep + ': already exists');
            continue;
        }
        const videoUrl = R2_PUBLIC + '/melolo/' + SLUG + '/ep' + String(ep).padStart(3, '0') + '.mp4';
        await p.episode.create({
            data: {
                dramaId: drama.id,
                episodeNumber: ep,
                title: 'Episode ' + ep,
                videoUrl: videoUrl,
                duration: 0,
                isActive: true,
            },
        });
        added++;
    }
    console.log('Added:', added, 'episodes');

    // Update totalEpisodes to 97
    await p.drama.update({
        where: { id: drama.id },
        data: { totalEpisodes: 97 },
    });
    console.log('Updated totalEpisodes to 97');

    // Verify final count
    const final = await p.episode.count({ where: { dramaId: drama.id } });
    console.log('Final episode count in DB:', final);

    await p.$disconnect();
}
main();
