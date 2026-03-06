const { PrismaClient } = require('@prisma/client');
const https = require('https');
const fs = require('fs');
const p = new PrismaClient();

const KEYWORDS = [
    '800 ribu', 'aku kaya dari giok', 'ahli pengobatan',
    'anak ajaib', 'bersinar setelah', 'kaya raya',
    'sang master turun', 'jam pasir', 'pewaris konglomerat', 'sesepuh tertua'
];

function headCheck(url) {
    return new Promise(resolve => {
        if (!url) return resolve('NULL');
        const req = https.request(url, { method: 'HEAD', timeout: 5000 }, res => resolve(String(res.statusCode)));
        req.on('error', () => resolve('ERR'));
        req.on('timeout', () => { req.destroy(); resolve('TMO'); });
        req.end();
    });
}

async function main() {
    const dramas = await p.drama.findMany({ where: { isActive: true }, select: { id: true, title: true, cover: true } });

    for (const kw of KEYWORDS) {
        const d = dramas.find(x => x.title.toLowerCase().includes(kw));
        if (!d) { process.stdout.write('NOTFOUND: ' + kw + '\n'); continue; }

        const ep = await p.episode.findFirst({
            where: { dramaId: d.id, isActive: true },
            select: { episodeNumber: true, videoUrl: true },
            orderBy: { episodeNumber: 'asc' },
        });

        const epSt = ep ? await headCheck(ep.videoUrl) : 'NO_EP';
        const icon = epSt === '200' ? 'OK' : 'FAIL';
        process.stdout.write(icon + ' | ' + d.title + ' | ep1=' + epSt + '\n');
    }

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
