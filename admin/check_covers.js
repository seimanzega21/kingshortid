const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function main() {
    const dramas = await p.drama.findMany({
        where: { isActive: true },
        select: { title: true, cover: true },
        orderBy: { createdAt: 'desc' },
    });

    // Categorize cover URL endings
    const endings = {};
    for (const d of dramas) {
        if (!d.cover) {
            if (!endings['NULL']) endings['NULL'] = [];
            endings['NULL'].push(d.title);
            continue;
        }
        const ext = d.cover.split('/').pop() || 'unknown';
        if (!endings[ext]) endings[ext] = [];
        endings[ext].push(d.title);
    }

    console.log('=== COVER FILE TYPES ===');
    for (const [ext, titles] of Object.entries(endings)) {
        console.log(`\n[${ext}] (${titles.length} dramas)`);
        titles.slice(0, 5).forEach(t => console.log(`  ${t}`));
        if (titles.length > 5) console.log(`  ... and ${titles.length - 5} more`);
    }

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
