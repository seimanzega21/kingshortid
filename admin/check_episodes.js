const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function main() {
    const targets = [
        '800 Ribu Beli Dunia Kultivasi',
        'Ahli Pengobatan Sakti',
        'Aku Kaya dari Giok',
        'Aku Tak Akan Mengejarmu Lagi',
        'Aku Tersesat di Dunia Kultivasi',
        'Anak Ajaib Ahli Barang Antik',
        'Antara Ambisi dan Cinta',
        'Ayah Berandalan jadi CEO',
        'Ayah Tiri Baru, Lindungi 6 Anak',
        'Balas Dendam Sang Putri Genius',
        'Balas Dendam pada Anak Angkat',
        'Bangkit Setelah Ditinggalkan',
        'Barang Supermarket di Dunia Kuno',
        'Bersinar Setelah Cerai',
        'Bos Datang Malah diajak Nguli',
    ];

    for (const title of targets) {
        const drama = await p.drama.findFirst({
            where: { title, isActive: true },
            include: { _count: { select: { episodes: true } } },
        });
        if (drama) {
            console.log(`${drama._count.episodes > 0 ? '[OK]' : '[!!]'} ${title}: ${drama._count.episodes} eps`);
        } else {
            console.log(`[--] ${title}: NOT FOUND`);
        }
    }

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
