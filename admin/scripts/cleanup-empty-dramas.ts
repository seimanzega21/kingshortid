import 'dotenv/config';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
    // Find all dramas with 0 episodes
    const dramas = await prisma.drama.findMany({
        include: { _count: { select: { episodes: true } } }
    });

    const empty = dramas.filter(d => d._count.episodes === 0);
    console.log(`\nDramas with 0 episodes in DB: ${empty.length}`);

    for (const d of empty) {
        // Delete related records first (cascade should handle most)
        await prisma.drama.delete({ where: { id: d.id } });
        console.log(`  Deleted: ${d.title}`);
    }

    const remaining = await prisma.drama.count();
    const epCount = await prisma.episode.count();
    console.log(`\nRemaining: ${remaining} dramas, ${epCount} episodes`);

    await prisma.$disconnect();
}

main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
