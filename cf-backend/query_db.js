const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
    const dramas = await prisma.drama.findMany({
        where: { title: { contains: 'Sang Abadi Menyamar' } },
        include: { episodes: { orderBy: { episodeNumber: 'asc' } } }
    });
    
    for (const d of dramas) {
        console.log(`\nFound Drama: ${d.title} (ID: ${d.id})`);
        
        // Find episode 13
        const ep13 = d.episodes.find(e => e.episodeNumber === 13);
        if (ep13) {
            console.log(`Episode 13 ID: ${ep13.id}`);
            console.log(`Episode 13 URL (720p): ${ep13.videoUrl720p}`);
            console.log(`Episode 13 URL (540p): ${ep13.videoUrl540p}`);
        } else {
            console.log("Episode 13 not found in DB.");
        }
    }
}

main().finally(() => prisma.$disconnect());
