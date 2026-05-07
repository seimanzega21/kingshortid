const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();
async function main() {
  const drama = await prisma.drama.findFirst({
    where: { title: { contains: 'Romantis di Musim Dingin', mode: 'insensitive' } },
    include: { episodes: { orderBy: { episodeNumber: 'asc' } } }
  });
  if (!drama) {
    console.log('Drama not found');
    return;
  }
  console.log('Drama ID:', drama.id);
  console.log('Total Episodes in DB:', drama.episodes.length);
  const ep32 = drama.episodes.find(e => e.episodeNumber === 32);
  if (ep32) {
    console.log('Episode 32 found:', JSON.stringify(ep32, null, 2));
  } else {
    console.log('Episode 32 MISSING');
  }
}
main().catch(console.error).finally(() => prisma.$disconnect());
