const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
  const deleted = await prisma.drama.deleteMany({
    where: { 
        OR: [
            { id: 'cha6iwjr8wxf6bivrkozgfhr' },
            { id: 'iq40fvxrnr2xx5f5hpk22ka5' },
            { id: 'v6f6u37yfuxz1pvkdqxh1o9p' },
            { id: 'p7a2xlr4twczf2zyk0lo1d9a' }
        ]
    }
  });
  console.log('Deleted count:', deleted.count);
}

main()
  .catch(e => console.error(e))
  .finally(async () => {
    await prisma.$disconnect();
  });
