import 'dotenv/config';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const R2_PUBLIC_URL = process.env.R2_PUBLIC_URL || 'https://stream.shortlovers.id';

async function main() {
    // Get all dramas with their first episode
    const dramas = await prisma.drama.findMany({
        include: {
            episodes: {
                take: 1,
                orderBy: { episodeNumber: 'asc' },
                select: { videoUrl: true },
            },
        },
    });

    console.log(`Checking ${dramas.length} dramas for video availability...\n`);

    let activeCount = 0;
    let deactivatedCount = 0;

    for (const drama of dramas) {
        const ep = drama.episodes[0];
        if (!ep?.videoUrl) {
            // No episodes at all — deactivate
            await prisma.drama.update({ where: { id: drama.id }, data: { isActive: false } });
            console.log(`  ❌ ${drama.title} — no episodes`);
            deactivatedCount++;
            continue;
        }

        // Check if the first segment is accessible
        // For HLS: replace playlist.m3u8 with segment_000.ts
        // For MP4: check the mp4 URL directly
        let checkUrl = ep.videoUrl;
        if (checkUrl.includes('playlist.m3u8')) {
            checkUrl = checkUrl.replace('playlist.m3u8', 'segment_000.ts');
        }

        try {
            const resp = await fetch(checkUrl, { method: 'HEAD', signal: AbortSignal.timeout(10000) });
            if (resp.ok) {
                await prisma.drama.update({ where: { id: drama.id }, data: { isActive: true } });
                activeCount++;
            } else {
                await prisma.drama.update({ where: { id: drama.id }, data: { isActive: false } });
                console.log(`  ❌ ${drama.title} — segment 404`);
                deactivatedCount++;
            }
        } catch {
            await prisma.drama.update({ where: { id: drama.id }, data: { isActive: false } });
            console.log(`  ❌ ${drama.title} — fetch error`);
            deactivatedCount++;
        }
    }

    console.log(`\n${'='.repeat(50)}`);
    console.log(`  Active (video ready): ${activeCount}`);
    console.log(`  Deactivated (incomplete): ${deactivatedCount}`);
    console.log(`${'='.repeat(50)}`);

    await prisma.$disconnect();
}

main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
