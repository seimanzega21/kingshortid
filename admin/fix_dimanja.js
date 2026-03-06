const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();
const R2_PUBLIC = 'https://stream.shortlovers.id';

async function main() {
    const drama = await p.drama.findFirst({ where: { title: { contains: 'Dimanja' } } });
    if (!drama) { process.stdout.write('Not found'); return; }

    const existing = await p.episode.count({ where: { dramaId: drama.id } });
    process.stdout.write('Dimanja: ' + existing + ' eps in DB, totalEpisodes=' + drama.totalEpisodes + '\n');

    // Register missing episodes (39-102)
    let added = 0;
    for (let i = 1; i <= 102; i++) {
        const exists = await p.episode.findUnique({
            where: { dramaId_episodeNumber: { dramaId: drama.id, episodeNumber: i } }
        });
        if (!exists) {
            await p.episode.create({
                data: {
                    dramaId: drama.id,
                    episodeNumber: i,
                    title: 'Episode ' + i,
                    videoUrl: R2_PUBLIC + '/melolo/dimanja-habis-habisan-oleh-bos/ep' + String(i).padStart(3, '0') + '.mp4',
                    duration: 0,
                    isActive: true,
                }
            });
            added++;
        }
    }

    // Update totalEpisodes
    await p.drama.update({ where: { id: drama.id }, data: { totalEpisodes: 102 } });
    process.stdout.write('Added ' + added + ' missing episodes\n');
    process.stdout.write('Total now: ' + (existing + added) + '/102\n');
    await p.$disconnect();
}
main().catch(e => { console.error(e); process.exit(1); });
