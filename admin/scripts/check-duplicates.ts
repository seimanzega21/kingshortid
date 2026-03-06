import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
    console.log('Checking for Duplicate Episodes...');

    // Find drama
    const drama = await prisma.drama.findFirst({
        where: { title: 'Takdir Di Balik Sandiwara' }
    });

    if (!drama) {
        console.log('Drama not found');
        return;
    }

    console.log(`Drama ID: ${drama.id}`);

    // Check records
    const eps = await prisma.episode.findMany({
        where: {
            dramaId: drama.id,
            episodeNumber: 1
        }
    });

    console.log(`Found ${eps.length} records for Episode 1:`);
    eps.forEach((e, i) => {
        console.log(`[${i}] ID: ${e.id}`);
        console.log(`    URL: ${e.videoUrl}`);
        console.log(`    Created: ${e.createdAt}`);
    });
}

main()
    .then(() => prisma.$disconnect())
    .catch((e) => {
        console.error(e);
        prisma.$disconnect();
    });
