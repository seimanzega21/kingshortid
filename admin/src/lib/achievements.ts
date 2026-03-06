import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// Achievement type definitions
export const ACHIEVEMENT_TYPES = {
    FIRST_WATCH: 'first_watch',
    BINGE_WATCHER: 'binge_watcher', // Watch 5 episodes in a day
    WEEK_STREAK: 'week_streak', // 7 day streak
    COIN_COLLECTOR: 'coin_collector', // Collect 1000 coins
    SOCIAL_BUTTERFLY: 'social_butterfly', // Share 10 times
    VIP_MEMBER: 'vip_member', // Become VIP
    COMPLETIONIST: 'completionist', // Finish a drama
    EARLY_BIRD: 'early_bird', // Watch new release within 24h
} as const;

/**
 * Check and unlock achievements for a user
 */
export async function checkAchievements(userId: string): Promise<string[]> {
    const unlockedAchievements: string[] = [];

    // Get user data with relations
    const user = await prisma.user.findUnique({
        where: { id: userId },
        include: {
            watchHistory: {
                orderBy: { watchedAt: 'desc' },
                take: 100,
            },
            coinTransactions: true,
            achievements: {
                include: { achievement: true },
            },
        },
    });

    if (!user) return [];

    // Get existing achievement IDs
    const existingAchievementIds = new Set(
        user.achievements.map((ua) => ua.achievement.type)
    );

    // Check first watch
    if (
        !existingAchievementIds.has(ACHIEVEMENT_TYPES.FIRST_WATCH) &&
        user.watchHistory.length > 0
    ) {
        await unlockAchievement(userId, ACHIEVEMENT_TYPES.FIRST_WATCH);
        unlockedAchievements.push(ACHIEVEMENT_TYPES.FIRST_WATCH);
    }

    // Check binge watcher (5+ episodes in last 24h)
    if (!existingAchievementIds.has(ACHIEVEMENT_TYPES.BINGE_WATCHER)) {
        const last24h = new Date(Date.now() - 24 * 60 * 60 * 1000);
        const recentWatches = user.watchHistory.filter(
            (wh) => wh.watchedAt >= last24h
        );
        if (recentWatches.length >= 5) {
            await unlockAchievement(userId, ACHIEVEMENT_TYPES.BINGE_WATCHER);
            unlockedAchievements.push(ACHIEVEMENT_TYPES.BINGE_WATCHER);
        }
    }

    // Check week streak
    if (
        !existingAchievementIds.has(ACHIEVEMENT_TYPES.WEEK_STREAK) &&
        user.checkInStreak >= 7
    ) {
        await unlockAchievement(userId, ACHIEVEMENT_TYPES.WEEK_STREAK);
        unlockedAchievements.push(ACHIEVEMENT_TYPES.WEEK_STREAK);
    }

    // Check coin collector (total earned >= 1000)
    if (!existingAchievementIds.has(ACHIEVEMENT_TYPES.COIN_COLLECTOR)) {
        const totalEarned = user.coinTransactions
            .filter((ct) => ct.type === 'earn' || ct.type === 'bonus')
            .reduce((sum, ct) => sum + ct.amount, 0);
        if (totalEarned >= 1000) {
            await unlockAchievement(userId, ACHIEVEMENT_TYPES.COIN_COLLECTOR);
            unlockedAchievements.push(ACHIEVEMENT_TYPES.COIN_COLLECTOR);
        }
    }

    // Check VIP member
    if (
        !existingAchievementIds.has(ACHIEVEMENT_TYPES.VIP_MEMBER) &&
        user.vipStatus
    ) {
        await unlockAchievement(userId, ACHIEVEMENT_TYPES.VIP_MEMBER);
        unlockedAchievements.push(ACHIEVEMENT_TYPES.VIP_MEMBER);
    }

    return unlockedAchievements;
}

/**
 * Unlock an achievement for a user
 */
async function unlockAchievement(
    userId: string,
    achievementType: string
): Promise<void> {
    // Find achievement by type
    const achievement = await prisma.achievement.findFirst({
        where: { type: achievementType, isActive: true },
    });

    if (!achievement) {
        console.error(`Achievement not found: ${achievementType}`);
        return;
    }

    // Create user achievement
    await prisma.userAchievement.create({
        data: {
            userId,
            achievementId: achievement.id,
        },
    });

    // Award coins if reward exists
    if (achievement.reward > 0) {
        await prisma.user.update({
            where: { id: userId },
            data: { coins: { increment: achievement.reward } },
        });

        // Record transaction
        await prisma.coinTransaction.create({
            data: {
                userId,
                type: 'bonus',
                amount: achievement.reward,
                description: `Achievement unlocked: ${achievement.name}`,
            },
        });
    }

    console.log(
        `Achievement unlocked: ${achievement.name} for user ${userId} (+${achievement.reward} coins)`
    );
}

/**
 * Initialize default achievements
 */
export async function seedAchievements(): Promise<void> {
    const achievements = [
        {
            name: 'Tontonan Pertama',
            description: 'Tonton drama pertama kamu',
            icon: '🎬',
            type: ACHIEVEMENT_TYPES.FIRST_WATCH,
            requirement: 1,
            reward: 10,
        },
        {
            name: 'Binge Watcher',
            description: 'Tonton 5 episode dalam sehari',
            icon: '🍿',
            type: ACHIEVEMENT_TYPES.BINGE_WATCHER,
            requirement: 5,
            reward: 50,
        },
        {
            name: 'Konsisten 7 Hari',
            description: 'Check-in 7 hari berturut-turut',
            icon: '🔥',
            type: ACHIEVEMENT_TYPES.WEEK_STREAK,
            requirement: 7,
            reward: 100,
        },
        {
            name: 'Kolektor Koin',
            description: 'Kumpulkan total 1000 koin',
            icon: '💰',
            type: ACHIEVEMENT_TYPES.COIN_COLLECTOR,
            requirement: 1000,
            reward: 200,
        },
        {
            name: 'Kupu-Kupu Sosial',
            description: 'Bagikan 10 drama ke teman',
            icon: '🦋',
            type: ACHIEVEMENT_TYPES.SOCIAL_BUTTERFLY,
            requirement: 10,
            reward: 75,
        },
        {
            name: 'VIP Member',
            description: 'Aktifkan membership VIP',
            icon: '💎',
            type: ACHIEVEMENT_TYPES.VIP_MEMBER,
            requirement: 1,
            reward: 150,
        },
        {
            name: 'Completionist',
            description: 'Selesaikan 1 drama hingga akhir',
            icon: '🏆',
            type: ACHIEVEMENT_TYPES.COMPLETIONIST,
            requirement: 1,
            reward: 100,
        },
        {
            name: 'Early Bird',
            description: 'Tonton rilis baru dalam 24 jam',
            icon: '🐦',
            type: ACHIEVEMENT_TYPES.EARLY_BIRD,
            requirement: 1,
            reward: 25,
        },
    ];

    for (const ach of achievements) {
        await prisma.achievement.upsert({
            where: { type: ach.type },
            update: ach,
            create: ach,
        });
    }

    console.log(`Seeded ${achievements.length} achievements`);
}
