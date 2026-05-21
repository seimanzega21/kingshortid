const { PrismaClient } = require('@prisma/client');

const DATABASE_URL = "postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres";
const prisma = new PrismaClient({
  datasources: {
    db: {
      url: DATABASE_URL,
    },
  },
});

async function main() {
    console.log('Testing direct DB connection to VPS public IP on port 5432...');
    try {
        const userCount = await prisma.user.count();
        console.log(`Connection successful! Total users in database: ${userCount}`);
        
        // Fetch one user to verify data read works
        const sampleUser = await prisma.user.findFirst({
            select: { id: true, email: true, role: true }
        });
        console.log('Sample user from DB:', sampleUser);
    } catch (err) {
        console.error('Direct connection failed:', err);
    } finally {
        await prisma.$disconnect();
    }
}

main();
