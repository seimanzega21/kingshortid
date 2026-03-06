/**
 * DATA QUALITY AUDIT v2 — Summary counts only
 */
const { PrismaClient } = require('@prisma/client');
require('dotenv').config();
const p = new PrismaClient();

async function main() {
    const dramas = await p.drama.findMany({
        where: { isActive: true },
        select: { id: true, title: true, cover: true, description: true, genres: true, totalEpisodes: true },
    });

    let noCover = 0, brokenCover = 0, badDesc = 0, genericGenre = 0, noEps = 0, noEp1 = 0, epGap = 0;
    const coverBroken = [];

    for (const d of dramas) {
        // Cover
        if (!d.cover || d.cover === '') {
            noCover++;
        } else {
            try {
                const r = await fetch(d.cover, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
                if (!r.ok) { brokenCover++; coverBroken.push(d.title + ' (' + r.status + ')'); }
            } catch { brokenCover++; coverBroken.push(d.title + ' (timeout)'); }
        }

        // Description
        if (!d.description || d.description === d.title || d.description.length < 10) badDesc++;

        // Genre
        if (!d.genres || d.genres.length === 0 || (d.genres.length === 1 && d.genres[0] === 'Drama')) genericGenre++;

        // Episodes
        const eps = await p.episode.findMany({
            where: { dramaId: d.id },
            select: { episodeNumber: true },
            orderBy: { episodeNumber: 'asc' },
        });
        if (eps.length === 0) { noEps++; continue; }
        if (eps[0].episodeNumber !== 1) noEp1++;
        for (let i = 1; i < eps.length; i++) {
            if (eps[i].episodeNumber !== eps[i - 1].episodeNumber + 1) { epGap++; break; }
        }
    }

    console.log('\n=== DATA QUALITY AUDIT ===');
    console.log('Total active dramas:', dramas.length);
    console.log('');
    console.log('COVER ISSUES:');
    console.log('  No cover URL:', noCover);
    console.log('  Broken cover (404/error):', brokenCover);
    if (coverBroken.length > 0) {
        console.log('  Broken list:');
        coverBroken.forEach(c => console.log('    - ' + c));
    }
    console.log('');
    console.log('METADATA ISSUES:');
    console.log('  Bad/missing descriptions:', badDesc);
    console.log('  Generic genre [Drama]:', genericGenre);
    console.log('');
    console.log('EPISODE ISSUES:');
    console.log('  No episodes at all:', noEps);
    console.log('  Missing episode 1:', noEp1);
    console.log('  Has episode gaps:', epGap);

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
