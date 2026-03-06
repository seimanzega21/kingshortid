import 'dotenv/config';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const R2 = 'https://stream.shortlovers.id';

const fixes = [
    { title: 'Lelaki Bermata Dewa', slug: 'lelaki-bermata-dewa' },
    { title: 'Mata Ajaib di Pasar Barang Antik', slug: 'mata-ajaib-di-pasar-barang-antik' },
    { title: 'Mata Kiri Ajaibku', slug: 'mata-kiri-ajaibku' },
    { title: 'Mata Sakti Mengungkap Rahasia', slug: 'mata-sakti-mengungkap-rahasia' },
    { title: 'Misi Cinta Sang Kurir', slug: 'misi-cinta-sang-kurir' },
];

async function main() {
    for (const { title, slug } of fixes) {
        const coverUrl = `${R2}/melolo/${slug}/poster.jpg`;
        const result = await prisma.drama.updateMany({
            where: { title: { contains: title, mode: 'insensitive' } },
            data: { cover: coverUrl },
        });
        console.log(`  ${title}: ${result.count} updated -> ${coverUrl}`);
    }
    await prisma.$disconnect();
}

main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
