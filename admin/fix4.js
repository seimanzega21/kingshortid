const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function main() {
    const dramas = await p.drama.findMany({ where: { isActive: true }, select: { id: true, title: true, cover: true } });

    // 1. Fix misi-cinta-sang-kurir: change episodes/XXX/ to epXXX/
    const misi = dramas.find(d => d.title.toLowerCase().includes('misi cinta sang kurir'));
    if (misi) {
        const eps = await p.episode.findMany({
            where: { dramaId: misi.id, isActive: true },
            select: { id: true, videoUrl: true }
        });
        let fixed = 0;
        for (const ep of eps) {
            if (!ep.videoUrl) continue;
            const newUrl = ep.videoUrl.replace(/\/episodes\/(\d+)\//, '/ep$1/');
            if (newUrl !== ep.videoUrl) {
                await p.episode.update({ where: { id: ep.id }, data: { videoUrl: newUrl } });
                fixed++;
            }
        }

        // Also fix cover URL if it uses wrong path
        // R2 has cover.jpg, check if DB cover points correctly
        const correctCover = 'https://stream.shortlovers.id/melolo/misi-cinta-sang-kurir/cover.jpg';
        if (misi.cover !== correctCover) {
            await p.drama.update({ where: { id: misi.id }, data: { cover: correctCover } });
            process.stdout.write('Fixed cover URL for Misi Cinta Sang Kurir\n');
        }

        process.stdout.write('Fixed ' + fixed + ' episode URLs for Misi Cinta Sang Kurir\n');
    }

    // 2. Deactivate 3 dramas with no R2 content
    const toDeactivate = ['kehadiran cinta dari masa lalu', 'mata kiri ajaibku', 'hidup berjaya anak terbuang'];
    for (const kw of toDeactivate) {
        const d = dramas.find(x => x.title.toLowerCase().includes(kw));
        if (d) {
            await p.drama.update({ where: { id: d.id }, data: { isActive: false } });
            process.stdout.write('Deactivated: ' + d.title + ' (no R2 content)\n');
        }
    }

    // 3. Verify misi-cinta fix
    if (misi) {
        const ep1 = await p.episode.findFirst({
            where: { dramaId: misi.id, isActive: true },
            orderBy: { episodeNumber: 'asc' },
            select: { videoUrl: true }
        });
        process.stdout.write('Misi ep1 URL: ' + (ep1 ? ep1.videoUrl : 'none') + '\n');
    }

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
