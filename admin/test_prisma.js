// Test Prisma findUnique directly
const { PrismaClient } = require('@prisma/client');
require('dotenv').config();

const prisma = new PrismaClient();

async function main() {
    const testId = '5decc22e-cf64-43f1-973f-e6573406e3ff';
    
    console.log('DATABASE_URL:', process.env.DATABASE_URL?.replace(/:[^:]+@/, ':***@'));
    
    // Test findUnique
    const drama = await prisma.drama.findUnique({
        where: { id: testId },
        select: { id: true, title: true, cover: true, totalEpisodes: true }
    });
    console.log('\nfindUnique result:', drama);
    
    // Test findMany with filter
    const dramas = await prisma.drama.findMany({
        where: { id: testId },
        select: { id: true, title: true }
    });
    console.log('findMany result:', dramas);
    
    // Test first few dramas
    const first5 = await prisma.drama.findMany({
        take: 5,
        orderBy: { createdAt: 'desc' },
        select: { id: true, title: true }
    });
    console.log('\nFirst 5 dramas:');
    first5.forEach(d => console.log(`  ${d.id} | ${d.title.substring(0, 40)}`));
    
    // Raw query test
    const raw = await prisma.$queryRaw`SELECT id, title FROM "Drama" WHERE id = ${testId}`;
    console.log('\nRaw query result:', raw);
    
    await prisma.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
