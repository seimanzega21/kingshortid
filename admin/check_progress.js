const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();
async function main() {
    const dramas = await p.drama.findMany({
        where: { isActive: true },
        select: { id: true, title: true, totalEpisodes: true, createdAt: true },
        orderBy: { createdAt: 'desc' },
    });
    let total_eps = 0;
    process.stdout.write('Total active dramas: ' + dramas.length + '\n\n');
    process.stdout.write('=== RECENTLY ADDED ===\n');
    for (const d of dramas.slice(0, 20)) {
        const eps = await p.episode.count({ where: { dramaId: d.id } });
        total_eps += eps;
        process.stdout.write(d.title + ' | ' + eps + '/' + d.totalEpisodes + ' eps | ' + d.createdAt.toISOString().slice(0, 16) + '\n');
    }
    process.stdout.write('\n--- Older dramas: ' + (dramas.length - 20) + ' more ---\n');
    for (const d of dramas.slice(20)) {
        const eps = await p.episode.count({ where: { dramaId: d.id } });
        total_eps += eps;
    }
    process.stdout.write('Total episodes in DB: ' + total_eps + '\n');
    await p.$disconnect();
}
main().catch(e => { console.error(e); process.exit(1); });
