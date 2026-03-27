const { PrismaClient } = require('@prisma/client');
const fs = require('fs');
const prisma = new PrismaClient();

async function main() {
    const dramas = await prisma.drama.findMany({
        where: {
            title: { contains: 'Pewaris', mode: 'insensitive' }
        },
        select: { id: true, title: true, cover: true, isActive: true }
    });
    
    fs.writeFileSync('pewaris_results.txt', dramas.map(d => 
        `${d.id} | ${d.title} | ${d.cover} | active:${d.isActive}`
    ).join('\n'), 'utf8');
    
    console.log('Done - wrote ' + dramas.length + ' results');
    await prisma.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
