const { PrismaClient } = require('@prisma/client');
const https = require('https');
const fs = require('fs');
const p = new PrismaClient();

const KEYWORDS = ['misi cinta sang kurir', 'kehadiran cinta', 'mata kiri', 'hidup berjaya'];

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

        const cs = d.cover ? await head(d.cover) : 'NULL_COVER';
        const e1s = eps.length > 0 ? await head(eps[0].videoUrl) : 'NO_EPS';
        const e1u = eps.length > 0 ? eps[0].videoUrl : 'none';

        lines.push(d.title);
        lines.push('  cover=' + cs + ' | eps=' + eps.length + ' | ep1=' + e1s);
        lines.push('  cover_url=' + (d.cover || 'NULL'));
        lines.push('  ep1_url=' + e1u);
        lines.push('');
    }

    fs.writeFileSync('diag4.txt', lines.join('\n'), 'utf8');
    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
