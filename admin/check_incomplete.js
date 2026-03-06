const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function main() {
    const dramas = await p.drama.findMany({
        where: { isActive: true },
        include: { _count: { select: { episodes: true } } }
    });

    const incomplete = dramas
        .filter(d => d._count.episodes < d.totalEpisodes)
        .map(d => ({
            title: d.title,
            have: d._count.episodes,
            need: d.totalEpisodes,
            missing: d.totalEpisodes - d._count.episodes
        }))
        .sort((a, b) => b.missing - a.missing);

    let totalMissing = 0;
    console.log('=== INCOMPLETE DRAMAS ===');
    incomplete.forEach(d => {
        console.log(`${d.title} | ${d.have}/${d.need} | missing: ${d.missing}`);
        totalMissing += d.missing;
    });
    console.log(`\nTotal missing episodes: ${totalMissing}`);
    console.log(`Incomplete dramas: ${incomplete.length}`);
    console.log(`\n--- Estimate ---`);
    console.log(`At ~30 sec/episode with 2 workers: ~${Math.ceil(totalMissing * 30 / 3600)} hours`);

    await p.$disconnect();
}

main();
