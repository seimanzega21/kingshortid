const { PrismaClient } = require('@prisma/client');
const https = require('https');
const fs = require('fs');
const p = new PrismaClient();

function head(url) {
    return new Promise(resolve => {
        if (!url) return resolve(-1);
        try {
            const req = https.request(url, { method: 'HEAD', timeout: 8000 }, res => resolve(res.statusCode));
            req.on('error', () => resolve(-2));
            req.on('timeout', () => { req.destroy(); resolve(-3); });
            req.end();
        } catch (e) { resolve(-4); }
    });
}

async function main() {
    const dramas = await p.drama.findMany({
        where: { isActive: true },
        select: { id: true, title: true, cover: true }
    });

    const broken = [];

    for (let i = 0; i < dramas.length; i++) {
        const d = dramas[i];
        try {
            const ep = await p.episode.findFirst({
                where: { dramaId: d.id, isActive: true },
                orderBy: { episodeNumber: 'asc' },
                select: { videoUrl: true }
            });

            if (!ep || !ep.videoUrl) {
                broken.push(d.title + ' | NO_EPISODES');
                continue;
            }

            const vs = await head(ep.videoUrl);
            const cs = await head(d.cover);

            if (vs !== 200 || cs !== 200) {
                broken.push(d.title + ' | cover=' + cs + ' ep1=' + vs);
            }
        } catch (e) {
            broken.push(d.title + ' | ERROR: ' + e.message);
        }
    }

    const result = 'BROKEN: ' + broken.length + '/' + dramas.length + '\n' + broken.join('\n');
    fs.writeFileSync('full_scan.txt', result, 'utf8');
    process.stdout.write(result + '\n');

    await p.$disconnect();
}

main().catch(e => { process.stderr.write(String(e) + '\n'); process.exit(1); });
