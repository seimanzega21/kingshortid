import 'dotenv/config';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
    const result = await prisma.episode.updateMany({
        where: { isVip: true },
        data: { isVip: false, coinPrice: 0 },
    });
    console.log(`Updated ${result.count} episodes to FREE (isVip=false, coinPrice=0)`);
    await prisma.$disconnect();
}

main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
