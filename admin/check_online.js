const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function main() {
    const users = await p.user.findMany({
        select: { name: true, updatedAt: true },
        orderBy: { updatedAt: 'asc' },
    });

    const now = Date.now();
    const h12ago = new Date(now - 12 * 60 * 60 * 1000);

    let online = 0;
    let offline = 0;

    users.forEach(u => {
        const hoursAgo = ((now - new Date(u.updatedAt).getTime()) / 3600000).toFixed(1);
        const status = new Date(u.updatedAt) >= h12ago ? 'ONLINE' : 'offline';
        if (status === 'ONLINE') online++; else offline++;
        console.log(`${status.padEnd(7)} ${u.name.substring(0, 22).padEnd(24)} ${hoursAgo}h ago`);
    });

    console.log(`\n--- TOTAL: ${online} online, ${offline} offline, ${users.length} total ---`);
    await p.$disconnect();
}
main();
