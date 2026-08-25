const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
  const updatedDrama = await prisma.drama.update({
    where: { id: 'iq40fvxrnr2xx5f5hpk22ka5' },
    data: {
      title: 'Sang CEO dan Tunangan Cleaning Service-nya',
      slug: 'sang-ceo-dan-tunangan-cleaning-service-nya'
    }
  });
  console.log('Updated:', updatedDrama.title);
}

main()
  .catch(e => console.error(e))
  .finally(async () => {
    await prisma.$disconnect();
  });
