const { PrismaClient } = require('@prisma/client');
const fs = require('fs');
const p = new PrismaClient();

// Fix video URLs: change /epXXX/ to /episodes/XXX/ for dramas where R2 uses old format
async function main() {
    const broken = JSON.parse(fs.readFileSync('broken_videos.json', 'utf8'));

    // Filter to only fixable ones (where old format returns 200)
    const fixable = broken.filter(b => b.fixedStatus === 200);
    process.stdout.write('Fixable: ' + fixable.length + ' / ' + broken.length + '\n');

    let fixed = 0;
    let failed = 0;

    for (const b of fixable) {
        // Get ALL episodes for this drama
        const episodes = await p.episode.findMany({
            where: { dramaId: b.dramaId, isActive: true },
            select: { id: true, videoUrl: true },
        });

        for (const ep of episodes) {
            if (!ep.videoUrl) continue;

            // Replace /epXXX/ with /episodes/XXX/
            const newUrl = ep.videoUrl.replace(/\/ep(\d+)\//, '/episodes/$1/');

            if (newUrl !== ep.videoUrl) {
                await p.episode.update({
                    where: { id: ep.id },
                    data: { videoUrl: newUrl },
                });
                fixed++;
            }
        }

        process.stdout.write('  Fixed: ' + b.title + ' (' + episodes.length + ' eps)\n');
    }

    // Handle unfixable
    const unfixable = broken.filter(b => b.fixedStatus !== 200);
    if (unfixable.length > 0) {
        process.stdout.write('\nUnfixable (' + unfixable.length + '):\n');
        unfixable.forEach(b => process.stdout.write('  ' + b.title + '\n'));
    }

    process.stdout.write('\nDone! Fixed ' + fixed + ' episode URLs across ' + fixable.length + ' dramas\n');

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
