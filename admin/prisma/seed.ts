import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function seedAchievements() {
    const achievements = [
        {
            name: 'Tontonan Pertama',
            description: 'Tonton drama pertama kamu',
            icon: '🎬',
            type: 'first_watch',
            requirement: 1,
            reward: 10,
        },
        {
            name: 'Binge Watcher',
            description: 'Tonton 5 episode dalam sehari',
            icon: '🍿',
            type: 'binge_watcher',
            requirement: 5,
            reward: 50,
        },
        {
            name: 'Konsisten 7 Hari',
            description: 'Check-in 7 hari berturut-turut',
            icon: '🔥',
            type: 'week_streak',
            requirement: 7,
            reward: 100,
        },
        {
            name: 'Kolektor Koin',
            description: 'Kumpulkan total 1000 koin',
            icon: '💰',
            type: 'coin_collector',
            requirement: 1000,
            reward: 200,
        },
        {
            name: 'Kupu-Kupu Sosial',
            description: 'Bagikan 10 drama ke teman',
            icon: '🦋',
            type: 'social_butterfly',
            requirement: 10,
            reward: 75,
        },
        {
            name: 'VIP Member',
            description: 'Aktifkan membership VIP',
            icon: '💎',
            type: 'vip_member',
            requirement: 1,
            reward: 150,
        },
        {
            name: 'Completionist',
            description: 'Selesaikan 1 drama hingga akhir',
            icon: '🏆',
            type: 'completionist',
            requirement: 1,
            reward: 100,
        },
        {
            name: 'Early Bird',
            description: 'Tonton rilis baru dalam 24 jam',
            icon: '🐦',
            type: 'early_bird',
            requirement: 1,
            reward: 25,
        },
    ];

    // Delete existing achievements first to avoid duplicates
    await prisma.achievement.deleteMany({});

    // Create new achievements
    for (const ach of achievements) {
        await prisma.achievement.create({
            data: ach,
        });
    }

    console.log(`✅ Seeded ${achievements.length} achievements`);
}

async function seedChallenges() {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const nextWeek = new Date(today);
    nextWeek.setDate(nextWeek.getDate() + 7);

    const challenges = [
        {
            title: 'Tonton 3 Episode Hari Ini',
            description: 'Selesaikan menonton 3 episode drama apa saja hari ini',
            icon: '🎬',
            type: 'daily',
            requirement: JSON.stringify({ type: 'watch_episodes', count: 3 }),
            reward: 20,
            startDate: today,
            endDate: tomorrow,
            isActive: true,
        },
        {
            title: 'Beruntun 5 Hari',
            description: 'Check-in selama 5 hari berturut-turut',
            icon: '🔥',
            type: 'daily',
            requirement: JSON.stringify({ type: 'check_in_streak', days: 5 }),
            reward: 50,
            startDate: today,
            endDate: nextWeek,
            isActive: true,
        },
        {
            title: 'Coba Genre Baru',
            description: 'Tonton drama dari genre yang belum pernah kamu tonton',
            icon: '🌟',
            type: 'daily',
            requirement: JSON.stringify({ type: 'watch_new_genre', count: 1 }),
            reward: 30,
            startDate: today,
            endDate: tomorrow,
            isActive: true,
        },
        {
            title: 'Bagikan ke Teman',
            description: 'Bagikan 2 drama favorit ke teman-temanmu',
            icon: '📱',
            type: 'daily',
            requirement: JSON.stringify({ type: 'share_drama', count: 2 }),
            reward: 25,
            startDate: today,
            endDate: tomorrow,
            isActive: true,
        },
        {
            title: 'Komentar Aktif',
            description: 'Tinggalkan 5 komentar di drama yang kamu tonton',
            icon: '💬',
            type: 'daily',
            requirement: JSON.stringify({ type: 'post_comments', count: 5 }),
            reward: 35,
            startDate: today,
            endDate: tomorrow,
            isActive: true,
        },
        {
            title: 'Challenge Mingguan: Binge Master',
            description: 'Selesaikan 1 drama lengkap minggu ini',
            icon: '🏆',
            type: 'weekly',
            requirement: JSON.stringify({ type: 'complete_drama', count: 1 }),
            reward: 150,
            startDate: today,
            endDate: nextWeek,
            isActive: true,
        },
        {
            title: 'Challenge Mingguan: Sosial Media Star',
            description: 'Bagikan 15 drama ke sosial media minggu ini',
            icon: '⭐',
            type: 'weekly',
            requirement: JSON.stringify({ type: 'share_drama', count: 15 }),
            reward: 100,
            startDate: today,
            endDate: nextWeek,
            isActive: true,
        },
    ];

    // Delete old challenges (older than 7 days)
    const deleteOlderThan = new Date(today);
    deleteOlderThan.setDate(deleteOlderThan.getDate() - 7);
    await prisma.challenge.deleteMany({
        where: {
            endDate: {
                lt: deleteOlderThan,
            },
        },
    });

    // Create new challenges
    for (const challenge of challenges) {
        await prisma.challenge.create({
            data: challenge,
        });
    }

    console.log(`✅ Seeded ${challenges.length} challenges`);
}

async function main() {
    console.log('🌱 Starting database seeding...');

    // Seed achievements
    console.log('📜 Seeding achievements...');
    await seedAchievements();

    // Seed challenges
    console.log('🎯 Seeding daily/weekly challenges...');
    await seedChallenges();

    // Seed categories
    console.log('📂 Seeding categories...');
    const categories = [
        { name: 'Romance', slug: 'romance', icon: '💕', order: 1 },
        { name: 'Action', slug: 'action', icon: '🎬', order: 2 },
        { name: 'Comedy', slug: 'comedy', icon: '😂', order: 3 },
        { name: 'Drama', slug: 'drama', icon: '😢', order: 4 },
        { name: 'Fantasy', slug: 'fantasy', icon: '✨', order: 5 },
        { name: 'Thriller', slug: 'thriller', icon: '😱', order: 6 },
        { name: 'Historical', slug: 'historical', icon: '🏛️', order: 7 },
        { name: 'School', slug: 'school', icon: '🎓', order: 8 },
    ];

    for (const cat of categories) {
        await prisma.category.upsert({
            where: { slug: cat.slug },
            update: cat,
            create: cat,
        });
    }

    console.log(`✅ Seeded ${categories.length} categories`);

    // Create sample admin user if not exists
    console.log('👤 Creating admin user...');
    const bcrypt = require('bcryptjs');
    const adminEmail = 'admin@kingshort.app';
    const existingAdmin = await prisma.user.findUnique({
        where: { email: adminEmail },
    });

    if (!existingAdmin) {
        const hashedPassword = await bcrypt.hash('admin123', 10);

        await prisma.user.create({
            data: {
                email: adminEmail,
                password: hashedPassword,
                name: 'Admin KingShort',
                role: 'admin',
                coins: 99999,
                vipStatus: true,
            },
        });
        console.log(`✅ Created admin user: ${adminEmail} / admin123`);
    } else {
        console.log('ℹ️  Admin user already exists');
    }

    console.log('✨ Seeding completed successfully!');
}

main()
    .catch((e) => {
        console.error('❌ Seeding failed:', e);
        process.exit(1);
    })
    .finally(async () => {
        await prisma.$disconnect();
    });
