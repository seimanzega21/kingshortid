import { getDb, parseJsonArray } from './src/db/index';
import { dramas, episodes } from './src/db/schema';
import { eq, desc, and, asc, sql } from 'drizzle-orm';

function enrichDrama(d: typeof dramas.$inferSelect) {
    let finalCover = d.cover;
    if (finalCover && finalCover.startsWith('/api/uploads')) {
        finalCover = `https://admin.shortlovers.id${finalCover}`;
    }

    return {
        ...d,
        cover: finalCover,
        genres: parseJsonArray(d.genres),
        tagList: parseJsonArray(d.tagList),
        cast: parseJsonArray(d.cast),
    };
}

async function main() {
    const db = getDb('http://141.11.160.187:8000', 'GoZViiH1AXLl73BqLdKDtpeGgwUzfW64');
    const allDramas = await db.select().from(dramas).where(eq(dramas.isActive, true)).orderBy(desc(dramas.views)).limit(500);

    const results = await Promise.all(
        allDramas.map(async (drama) => {
            const firstEp = await db.select().from(episodes)
                .where(and(eq(episodes.dramaId, drama.id), sql`"episodes"."video_url" IS NOT NULL`))
                .orderBy(asc(episodes.episodeNumber))
                .limit(1)
                .then(r => r[0]);

            if (!firstEp?.videoUrl) return null;
            return {
                ...enrichDrama(drama),
                episodes: [{
                    id: firstEp.id,
                    videoUrl: firstEp.videoUrl,
                    episodeNumber: firstEp.episodeNumber,
                    title: firstEp.title,
                    duration: firstEp.duration,
                }],
            };
        })
    );

    const available = results.filter(Boolean) as NonNullable<typeof results[0]>[];

    try {
        const availableSortedByNew = [...available].sort((a, b) => {
            if (!a.createdAt || !b.createdAt) throw new Error("Missing createdAt");
            return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
        });
        
        const newDramas = availableSortedByNew.slice(0, 20);
        const newDramaIds = new Set(newDramas.map(d => d.id));
        const otherDramas = available.filter(d => !newDramaIds.has(d.id));

        const seedNum = Date.now();
        const shuffleArray = (arr: any[]) => {
            const shuffled = [...arr];
            for (let i = shuffled.length - 1; i > 0; i--) {
                const j = Math.floor(((seedNum * (i + 1) * 9301 + 49297) % 233280) / 233280 * (i + 1));
                [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
            }
            return shuffled;
        };

        const shuffledNew = shuffleArray(newDramas);
        const shuffledOther = shuffleArray(otherDramas);

        const mixedFeed = [];
        let newIdx = 0;
        let otherIdx = 0;
        
        while (newIdx < shuffledNew.length || otherIdx < shuffledOther.length) {
            if (newIdx < shuffledNew.length) {
                mixedFeed.push(shuffledNew[newIdx++]);
            }
            for (let i = 0; i < 3 && otherIdx < shuffledOther.length; i++) {
                mixedFeed.push(shuffledOther[otherIdx++]);
            }
        }
        console.log('Mixed successfully, size:', mixedFeed.length);
        process.exit(0);
    } catch (e) {
        console.error('Error during sort:', e);
        process.exit(1);
    }
}
main().catch(console.error);
