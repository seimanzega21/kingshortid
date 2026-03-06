const { PrismaClient } = require('@prisma/client');
require('dotenv').config();
const p = new PrismaClient();

async function main() {
    const d = await p.drama.findFirst({ where: { title: { contains: 'Asisten yang Ternyata' } } });
    console.log('Title:', d.title);
    console.log('ID:', d.id);
    console.log('totalEpisodes field:', d.totalEpisodes);

    const eps = await p.episode.findMany({
        where: { dramaId: d.id },
        select: { episodeNumber: true, videoUrl: true },
        orderBy: { episodeNumber: 'asc' },
    });
    console.log('Actual episodes in DB:', eps.length);
    console.log('Numbers:', eps.map(e => e.episodeNumber).join(', '));

    const nums = eps.map(e => e.episodeNumber);
    for (let i = 1; i < nums.length; i++) {
        if (nums[i] - nums[i - 1] > 1)
            console.log('GAP: ep' + nums[i - 1] + ' -> ep' + nums[i] + ' (missing ' + (nums[i] - nums[i - 1] - 1) + ')');
    }

    // Check which episodes 1-97 are missing
    const numSet = new Set(nums);
    const missing = [];
    for (let i = 1; i <= 97; i++) {
        if (!numSet.has(i)) missing.push(i);
    }
    console.log('\nMissing episodes:', missing.join(', '));
    console.log('Total missing:', missing.length);

    await p.$disconnect();
}
main();
