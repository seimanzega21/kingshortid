const { PrismaClient } = require('@prisma/client');
require('dotenv').config();
const p = new PrismaClient();

async function main() {
    const d = await p.drama.findFirst({
        where: { title: { contains: 'Misi Cinta' } },
        select: { id: true, title: true, totalEpisodes: true }
    });
    console.log('Drama:', JSON.stringify(d, null, 2));

    const eps = await p.episode.findMany({
        where: { dramaId: d.id },
        orderBy: { episodeNumber: 'asc' },
        select: { episodeNumber: true, videoUrl: true }
    });
    console.log('\nTotal episodes in DB:', eps.length);
    console.log('\nFirst 5:');
    eps.slice(0, 5).forEach(e => console.log(`  Ep ${e.episodeNumber}: ${e.videoUrl}`));
    console.log('\nLast 3:');
    eps.slice(-3).forEach(e => console.log(`  Ep ${e.episodeNumber}: ${e.videoUrl}`));

    // Check for broken URLs (empty, null, or non-R2)
    const broken = eps.filter(e => !e.videoUrl || e.videoUrl.includes('sample'));
    if (broken.length > 0) {
        console.log('\n⚠️ Broken/empty URLs:', broken.length);
        broken.forEach(e => console.log(`  Ep ${e.episodeNumber}: ${e.videoUrl || 'NULL'}`));
    }

    // Check URL pattern consistency
    const patterns = {};
    eps.forEach(e => {
        if (e.videoUrl) {
            const domain = e.videoUrl.split('/')[2] || 'unknown';
            patterns[domain] = (patterns[domain] || 0) + 1;
        }
    });
    console.log('\nURL patterns:', patterns);

    await p.$disconnect();
}
main().catch(e => { console.error(e); process.exit(1); });
