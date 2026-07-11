import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  try {
    const usersCount = await prisma.user.count();
    console.log('Users:', usersCount);

    const dramasCount = await prisma.drama.count();
    console.log('Dramas:', dramasCount);

    const views = await prisma.drama.aggregate({ _sum: { views: true } });
    console.log('Views:', views._sum.views);

    const watchHistoryCount = await prisma.watchHistory.count();
    console.log('Watch History:', watchHistoryCount);

    const coinTransactions = await prisma.coinTransaction.aggregate({
      _sum: { amount: true },
      where: { type: 'topup' }
    });
    console.log('Coin Transactions (topup):', coinTransactions._sum.amount);
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await prisma.$disconnect();
  }
}

main();
