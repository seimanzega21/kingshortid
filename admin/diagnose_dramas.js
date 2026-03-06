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
    const lines = [];

    for (const kw of KEYWORDS) {
        const d = dramas.find(x => x.title.toLowerCase().includes(kw));
        if (!d) { lines.push('NOTFOUND: ' + kw); continue; }

        const eps = await p.episode.findMany({
            where: { dramaId: d.id, isActive: true },
            select: { episodeNumber: true, videoUrl: true },
            orderBy: { episodeNumber: 'asc' }
        });

        const coverSt = await headCheck(d.cover);
        const ep1St = eps.length > 0 ? await headCheck(eps[0].videoUrl) : 'NO_EPS';
        const ep1Url = eps.length > 0 ? eps[0].videoUrl : 'none';

        lines.push(d.title);
        lines.push('  cover=' + coverSt + ' | eps=' + eps.length + ' | ep1_status=' + ep1St);
        lines.push('  ep1_url=' + ep1Url);
        lines.push('  cover_url=' + d.cover);
        lines.push('');
    }

    fs.writeFileSync('diagnose_output.txt', lines.join('\n'), 'utf8');
    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
