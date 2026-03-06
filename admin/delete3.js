const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function main() {
    const titles = [
        'Kehadiran Cinta dari Masa Lalu',
        'Mata Kiri Ajaibku',
        'Hidup Berjaya Anak Terbuang',
    ];

    for (const t of titles) {
        const d = await p.drama.findFirst({ where: { title: t } });
        if (!d) { process.stdout.write('Not found: ' + t + '\n'); continue; }

        // Delete episodes first (foreign key)
        const del = await p.episode.deleteMany({ where: { dramaId: d.id } });
        // Delete drama
        await p.drama.delete({ where: { id: d.id } });
        process.stdout.write('Deleted: ' + t + ' (' + del.count + ' episodes)\n');
    }

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
