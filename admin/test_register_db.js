const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');
require('dotenv').config();

const prisma = new PrismaClient();

async function main() {
    console.log('Testing User Creation via Prisma...');
    const email = 'test_register_' + Date.now() + '@example.com';
    const password = 'testpassword123';
    const hashedPassword = await bcrypt.hash(password, 10);
    const name = 'Test Admin User';

    try {
        const user = await prisma.user.create({
            data: {
                name,
                email,
                password: hashedPassword,
                provider: 'local',
                role: 'admin',
                coins: 999999,
            },
        });
        console.log('Successfully created user:', user);
    } catch (err) {
        console.error('Failed to create user:', err);
    } finally {
        await prisma.$disconnect();
    }
}

main();
