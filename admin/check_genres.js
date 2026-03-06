const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function main() {
    // Check genres for recent dramas
    const dramas = await p.drama.findMany({
        where: { isActive: true },
        select: { title: true, genres: true, description: true },
        orderBy: { createdAt: 'desc' },
        take: 15
    });

    console.log('=== RECENT DRAMAS - GENRE CHECK ===\n');
    for (const d of dramas) {
        const desc = d.description ? d.description.substring(0, 40) + '...' : 'NO DESC';
        const genres = d.genres && d.genres.length > 0 ? d.genres.join(', ') : '❌ EMPTY';
        console.log(`${d.title}`);
        console.log(`  Genres: ${genres}`);
        console.log(`  Desc: ${desc}\n`);
    }

    // Count dramas with empty genres
    const all = await p.drama.findMany({ where: { isActive: true }, select: { genres: true } });
    const emptyGenres = all.filter(d => !d.genres || d.genres.length === 0).length;
    console.log(`\nTotal: ${all.length} dramas | Empty genres: ${emptyGenres}`);

    await p.$disconnect();
}
main().catch(e => { console.error(e); process.exit(1); });
