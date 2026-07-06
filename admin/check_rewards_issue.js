const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function main() {
    console.log("=== RECENT UPDATED USERS ===");
    const users = await p.user.findMany({
        orderBy: { updatedAt: 'desc' },
        take: 5,
        select: {
            id: true,
            email: true,
            name: true,
            coins: true,
            createdAt: true,
            updatedAt: true
        }
    });

    for (const u of users) {
        console.log(`\nUser: ${u.name} (${u.email}) | ID: ${u.id}`);
        console.log(`  Coins: ${u.coins}`);
        console.log(`  Created: ${u.createdAt}`);
        console.log(`  Updated: ${u.updatedAt}`);

        // Get daily rewards
        const daily = await p.dailyReward.findMany({
            where: { userId: u.id },
            orderBy: { claimedAt: 'desc' },
            take: 5
        });
        console.log(`  Daily Rewards (last 5):`);
        if (daily.length === 0) {
            console.log("    None");
        } else {
            daily.forEach(d => {
                console.log(`    - ID: ${d.id} | Type: ${d.rewardType} | Amount: ${d.amount} | ClaimedAt: ${d.claimedAt}`);
            });
        }

        // Get transactions
        const txs = await p.coinTransaction.findMany({
            where: { userId: u.id },
            orderBy: { createdAt: 'desc' },
            take: 5
        });
        console.log(`  Coin Transactions (last 5):`);
        if (txs.length === 0) {
            console.log("    None");
        } else {
            txs.forEach(t => {
                console.log(`    - ID: ${t.id} | Type: ${t.type} | Amount: ${t.amount} | Desc: ${t.description} | CreatedAt: ${t.createdAt}`);
            });
        }
    }

    await p.$disconnect();
}

main().catch(e => {
    console.error(e);
    process.exit(1);
});
