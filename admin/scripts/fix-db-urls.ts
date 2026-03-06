import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const NEW_DOMAIN = 'https://stream.shortlovers.id';
// Old domain we want to replace (the one I mistakenly set)
const OLD_DOMAIN_PART = 'pub-shortlovers.r2.dev';

async function updateUrls() {
    console.log('🔄 Updating Database URLs...');

    const episodes = await prisma.episode.findMany({
        where: {
            videoUrl: {
                contains: OLD_DOMAIN_PART
            }
        }
    });

    console.log(`Found ${episodes.length} episodes with old domain.`);

    for (const ep of episodes) {
        // Replace old domain with new domain
        const newUrl = ep.videoUrl.replace(OLD_DOMAIN_PART, 'stream.shortlovers.id');

        await prisma.episode.update({
            where: { id: ep.id },
            data: { videoUrl: newUrl }
        });

        console.log(`Updated EP ${ep.episodeNumber}: ${newUrl}`);
    }

    console.log('✅ Update Complete');
}

updateUrls()
    .then(() => prisma.$disconnect())
    .catch((e) => {
        console.error(e);
        prisma.$disconnect();
    });
