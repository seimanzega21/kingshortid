const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function main() {
    const dramaId = 'cmlficdq400twldfkj1c0ei2f'; // Dokter Genius Pujaan Hati

    // Get all episodes
    const episodes = await p.episode.findMany({
        where: { dramaId, isActive: true },
        select: { id: true, episodeNumber: true, videoUrl: true },
        orderBy: { episodeNumber: 'asc' },
    });

    process.stdout.write('Total episodes: ' + episodes.length + '\n');
    process.stdout.write('First ep: ' + episodes[0].episodeNumber + ' -> ' + episodes[0].videoUrl + '\n');
    process.stdout.write('Last ep: ' + episodes[episodes.length - 1].episodeNumber + ' -> ' + episodes[episodes.length - 1].videoUrl + '\n\n');

    // Fix: change /epXXX/ to /episodes/XXX/ AND shift by +1 (ep001->episodes/002)
    let fixed = 0;
    for (const ep of episodes) {
        if (!ep.videoUrl) continue;

        // Extract episode number from URL and add 1
        const match = ep.videoUrl.match(/\/ep(\d+)\//);
        if (match) {
            const oldNum = match[1];
            const newNum = String(parseInt(oldNum) + 1).padStart(3, '0');
            const newUrl = ep.videoUrl.replace(/\/ep\d+\//, '/episodes/' + newNum + '/');

            await p.episode.update({
                where: { id: ep.id },
                data: { videoUrl: newUrl },
            });
            fixed++;
        }
    }

    process.stdout.write('Fixed ' + fixed + ' episodes\n');

    // Verify first episode
    const check = await p.episode.findFirst({
        where: { dramaId, isActive: true },
        orderBy: { episodeNumber: 'asc' },
    });
    process.stdout.write('Verified first: ' + check.videoUrl + '\n');

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
