const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function main() {
    const ds = await p.drama.findMany({
        orderBy: { createdAt: 'desc' },
        take: 5,
        select: { id: true, title: true, cover: true, description: true, totalEpisodes: true, createdAt: true }
    });

    for (const d of ds) {
        const c = await p.episode.count({ where: { dramaId: d.id } });
        const hasDesc = d.description ? 'yes' : 'NULL';
        const hasCover = d.cover ? d.cover.substring(0, 50) : 'NULL';
        process.stdout.write(d.title + '\n');
        process.stdout.write('  id=' + d.id + '\n');
        process.stdout.write('  eps_db=' + c + '\n');
        process.stdout.write('  desc=' + hasDesc + '\n');
        process.stdout.write('  cover=' + hasCover + '\n\n');
    }

    await p.$disconnect();
}
main().catch(e => { console.error(e); process.exit(1); });
