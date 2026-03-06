import 'dotenv/config';
import { PrismaClient } from '@prisma/client';
const p = new PrismaClient();

async function main() {
    const d = await p.drama.findUnique({
        where: { id: 'cmleexukt0383hx5ewjk5efxh' },
        select: { title: true, description: true, genres: true, isActive: true }
    });
    console.log('DB state:');
    console.log(`  Title: "${d?.title}"`);
    console.log(`  Description: "${d?.description?.substring(0, 100)}..."`);
    console.log(`  Genres: ${JSON.stringify(d?.genres)}`);
    console.log(`  Active: ${d?.isActive}`);
    await p.$disconnect();
}
main();
