const { PrismaClient } = require('@prisma/client');
const https = require('https');
const fs = require('fs');
const p = new PrismaClient();

function headCheck(url) {
    return new Promise(resolve => {
        if (!url) return resolve('NULL');
        const req = https.request(url, { method: 'HEAD', timeout: 5000 }, res => resolve(res.statusCode));
        req.on('error', () => resolve('ERR'));
        req.on('timeout', () => { req.destroy(); resolve('TMO'); });
        req.end();
    });
}

async function main() {
    // Get all active dramas
    const dramas = await p.drama.findMany({
        where: { isActive: true },
        select: { id: true, title: true },
    });

    const broken = [];
    const lines = [];

    for (let i = 0; i < dramas.length; i++) {
        const d = dramas[i];
        // Get first episode
        const ep = await p.episode.findFirst({
            where: { dramaId: d.id, isActive: true },
            select: { id: true, episodeNumber: true, videoUrl: true },
            orderBy: { episodeNumber: 'asc' },
        });

        if (!ep || !ep.videoUrl) continue;

        // Check if URL uses epXXX format (new) 
        if (ep.videoUrl.includes('/ep0') || ep.videoUrl.includes('/ep1')) {
            // Check if it's actually a 404
            const status = await headCheck(ep.videoUrl);
            if (status === 404) {
                // Try the old format
                const oldUrl = ep.videoUrl.replace(/\/ep(\d+)\//, '/episodes/$1/');
                const oldStatus = await headCheck(oldUrl);
                broken.push({
                    title: d.title,
                    dramaId: d.id,
                    currentUrl: ep.videoUrl,
                    fixedUrl: oldUrl,
                    currentStatus: status,
                    fixedStatus: oldStatus,
                });
                lines.push(d.title + ': ' + status + ' -> ' + oldStatus);
            }
        }

        if ((i + 1) % 20 === 0) {
            lines.push('... checked ' + (i + 1) + '/' + dramas.length);
        }
    }

    lines.push('');
    lines.push('TOTAL BROKEN: ' + broken.length);
    lines.push('');
    for (const b of broken) {
        lines.push(b.title + ': ' + b.currentStatus + ' -> ' + b.fixedStatus);
        lines.push('  FROM: ' + b.currentUrl);
        lines.push('  TO:   ' + b.fixedUrl);
    }

    fs.writeFileSync('broken_videos.txt', lines.join('\n'), 'utf8');

    // Also save as JSON for the fix script
    fs.writeFileSync('broken_videos.json', JSON.stringify(broken, null, 2), 'utf8');

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
