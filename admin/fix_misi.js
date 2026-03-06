const { PrismaClient } = require('@prisma/client');
const https = require('https');
const p = new PrismaClient();

function head(url) {
    return new Promise(resolve => {
        if (!url) return resolve('NULL');
        const req = https.request(url, { method: 'HEAD', timeout: 5000 }, res => resolve(res.statusCode));
        req.on('error', () => resolve('ERR'));
        req.on('timeout', () => { req.destroy(); resolve('TMO'); });
        req.end();
    });
}

async function main() {
    // Get misi-cinta episodes
    const d = await p.drama.findFirst({ where: { title: { contains: 'Misi Cinta' }, isActive: true } });
    if (!d) { process.stdout.write('Not found\n'); return; }

    const eps = await p.episode.findMany({
        where: { dramaId: d.id, isActive: true },
        select: { id: true, episodeNumber: true, videoUrl: true },
        orderBy: { episodeNumber: 'asc' },
        take: 5
    });

    process.stdout.write('Drama: ' + d.title + '\n');
    for (const ep of eps) {
        process.stdout.write('  ep' + ep.episodeNumber + ': ' + ep.videoUrl + '\n');
    }

    // The R2 has ep001/playlist.m3u8 format, but DB has episodes/002.mp4
    // Fix: change all episodes to epXXX/playlist.m3u8 format with correct numbering
    const allEps = await p.episode.findMany({
        where: { dramaId: d.id, isActive: true },
        select: { id: true, episodeNumber: true, videoUrl: true },
        orderBy: { episodeNumber: 'asc' }
    });

    let fixed = 0;
    for (const ep of allEps) {
        if (!ep.videoUrl) continue;
        const padded = String(ep.episodeNumber).padStart(3, '0');
        const newUrl = 'https://stream.shortlovers.id/melolo/misi-cinta-sang-kurir/ep' + padded + '/playlist.m3u8';

        if (ep.videoUrl !== newUrl) {
            await p.episode.update({ where: { id: ep.id }, data: { videoUrl: newUrl } });
            fixed++;
        }
    }

    process.stdout.write('\nFixed ' + fixed + ' episode URLs\n');

    // Verify first ep
    const newEp1 = await p.episode.findFirst({
        where: { dramaId: d.id, isActive: true },
        orderBy: { episodeNumber: 'asc' }
    });
    const status = await head(newEp1.videoUrl);
    process.stdout.write('Verified ep1: ' + status + ' -> ' + newEp1.videoUrl + '\n');

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
