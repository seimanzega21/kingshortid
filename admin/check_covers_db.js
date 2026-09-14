const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function main() {
    const titles = [
        'Pengantin Sang Raja Serigala',
        'Gairah Terlarang',
        'Isi Hatiku Bocor Ibu Menang Telak',
        '(Dub) Bangkitnya Penguasa Sakti',
        'Ayah, Identitasmu Terungkap!',
        'Menaklukkan Paman Shawn',
        'Aku Bercinta dengan Bos Mafia'
    ];

    for (const t of titles) {
        const drama = await p.drama.findFirst({
            where: { title: { contains: t, mode: 'insensitive' } },
            select: { id: true, title: true, cover: true }
        });
        if (drama) {
            console.log(`[${drama.id}] "${drama.title}" => cover: "${drama.cover}"`);
        } else {
            console.log(`NOT FOUND: ${t}`);
        }
    }
    await p.$disconnect();
}
main().catch(console.error);
