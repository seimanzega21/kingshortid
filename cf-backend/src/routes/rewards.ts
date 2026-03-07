import { Hono } from 'hono';
import { eq, and, sql, desc, gte } from 'drizzle-orm';
import { getDb } from '../db';
import { users, coinTransactions, dailyRewards, watchHistory, achievements, userAchievements } from '../db/schema';
import { Env, requireAuth } from '../middleware/auth';

const rewardsRoute = new Hono<Env>();
rewardsRoute.use('*', requireAuth);

const STREAK_BONUSES = [
    { day: 1, coins: 10 },
    { day: 2, coins: 15 },
    { day: 3, coins: 20 },
    { day: 4, coins: 25 },
    { day: 5, coins: 30 },
    { day: 6, coins: 40 },
    { day: 7, coins: 100 },
];

function toWIBDateString(date: Date): string {
    // WIB = UTC+7, offset 7 hours
    const wib = new Date(date.getTime() + 7 * 60 * 60 * 1000);
    return wib.toISOString().slice(0, 10); // YYYY-MM-DD in WIB
}

function isSameDay(date1: Date, date2: Date): boolean {
    return toWIBDateString(date1) === toWIBDateString(date2);
}

// POST /api/rewards/check-in
rewardsRoute.post('/check-in', async (c) => {
    try {
        const userId = c.get('user').id;
        const now = new Date();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        if (user.lastCheckIn && isSameDay(new Date(user.lastCheckIn), now)) {
            return c.json({ error: 'Already checked in today', streak: user.checkInStreak }, 400);
        }

        let newStreak = 1;
        if (user.lastCheckIn) {
            const yesterday = new Date(now);
            yesterday.setDate(yesterday.getDate() - 1);
            const lastCheckInDate = new Date(user.lastCheckIn);
            if (isSameDay(lastCheckInDate, yesterday)) {
                newStreak = (user.checkInStreak % 7) + 1;
            }
        }

        const bonusInfo = STREAK_BONUSES.find(b => b.day === newStreak) || STREAK_BONUSES[0];
        const newBalance = user.coins + bonusInfo.coins;

        await db.update(users).set({
            coins: newBalance,
            lastCheckIn: now,
            checkInStreak: newStreak,
            updatedAt: now,
        }).where(eq(users.id, userId));

        await db.insert(coinTransactions).values({
            userId,
            type: 'bonus',
            amount: bonusInfo.coins,
            description: `Check-In Hari ke-${newStreak}`,
            balanceAfter: newBalance,
        });

        await db.insert(dailyRewards).values({
            userId,
            rewardType: 'check_in',
            amount: bonusInfo.coins,
        });

        return c.json({
            success: true,
            streak: newStreak,
            reward: bonusInfo.coins,
            newBalance,
            isWeeklyBonus: newStreak === 7,
        });
    } catch (error) {
        console.error('Check-in error:', error);
        return c.json({ error: 'Failed to check in' }, 500);
    }
});

// GET /api/rewards/status
rewardsRoute.get('/status', async (c) => {
    try {
        const userId = c.get('user').id;
        const now = new Date();
        const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        const canCheckIn = !user.lastCheckIn || !isSameDay(new Date(user.lastCheckIn), now);

        const dailyEpisodesResult = await db.select({ count: sql<number>`count(*)` }).from(watchHistory)
            .where(and(eq(watchHistory.userId, userId), gte(watchHistory.watchedAt, todayStart)));
        const dailyEpisodesWatched = dailyEpisodesResult[0]?.count || 0;

        const claimedDailyRewardsResult = await db.select().from(dailyRewards)
            .where(and(
                eq(dailyRewards.userId, userId),
                sql`${dailyRewards.rewardType} LIKE 'watch_%'`,
                gte(dailyRewards.claimedAt, todayStart),
            ));
        const claimedDailyTasks = claimedDailyRewardsResult.map(r => r.rewardType.replace('watch_', ''));

        // Check if user has rated the app (lifetime, not daily)
        const rateAppClaim = await db.select().from(dailyRewards)
            .where(and(
                eq(dailyRewards.userId, userId),
                eq(dailyRewards.rewardType, 'rate_app'),
            ))
            .limit(1).then((r: any[]) => r[0]);
        const hasRatedApp = !!rateAppClaim;

        return c.json({
            coins: user.coins,
            canCheckIn,
            checkInStreak: user.checkInStreak,
            lastCheckIn: user.lastCheckIn,
            dailyEpisodesWatched,
            claimedDailyTasks,
            hasRatedApp,
        });
    } catch (error) {
        console.error('Get status error:', error);
        return c.json({ error: 'Failed to get status' }, 500);
    }
});

// POST /api/rewards/claim-watch
rewardsRoute.post('/claim-watch', async (c) => {
    try {
        const userId = c.get('user').id;
        const { taskId } = await c.req.json();
        const now = new Date();
        const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const validTasks: Record<string, { target: number; bonus: number }> = {
            watch5: { target: 5, bonus: 20 },
            watch10: { target: 10, bonus: 40 },
        };

        const task = validTasks[taskId];
        if (!task) return c.json({ error: 'Invalid task' }, 400);

        const existingClaim = await db.select().from(dailyRewards)
            .where(and(
                eq(dailyRewards.userId, userId),
                eq(dailyRewards.rewardType, `watch_${taskId}`),
                gte(dailyRewards.claimedAt, todayStart),
            ))
            .limit(1).then((r: any[]) => r[0]);

        if (existingClaim) return c.json({ error: 'Already claimed today' }, 400);

        const watchedResult = await db.select({ count: sql<number>`count(*)` }).from(watchHistory)
            .where(and(eq(watchHistory.userId, userId), gte(watchHistory.watchedAt, todayStart)));
        const watchedCount = watchedResult[0]?.count || 0;

        if (watchedCount < task.target) {
            return c.json({ error: `Need ${task.target} episodes, watched ${watchedCount}` }, 400);
        }

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        const newBalance = user.coins + task.bonus;

        await db.update(users).set({ coins: newBalance, updatedAt: now }).where(eq(users.id, userId));

        await db.insert(coinTransactions).values({
            userId,
            type: 'earn',
            amount: task.bonus,
            description: `Hadiah Menonton: ${task.target} episode`,
            balanceAfter: newBalance,
        });

        await db.insert(dailyRewards).values({
            userId,
            rewardType: `watch_${taskId}`,
            amount: task.bonus,
        });

        return c.json({ success: true, bonus: task.bonus, newBalance });
    } catch (error) {
        console.error('Claim watch error:', error);
        return c.json({ error: 'Failed to claim watch reward' }, 500);
    }
});

// POST /api/rewards/claim-rate — One-time reward for rating app on Google Play
rewardsRoute.post('/claim-rate', async (c) => {
    try {
        const userId = c.get('user').id;
        const now = new Date();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        // Check if already claimed (lifetime, not daily)
        const existingClaim = await db.select().from(dailyRewards)
            .where(and(
                eq(dailyRewards.userId, userId),
                eq(dailyRewards.rewardType, 'rate_app'),
            ))
            .limit(1).then((r: any[]) => r[0]);

        if (existingClaim) {
            return c.json({ error: 'Already claimed rate reward' }, 400);
        }

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        const bonus = 100;
        const newBalance = user.coins + bonus;

        await db.update(users).set({ coins: newBalance, updatedAt: now }).where(eq(users.id, userId));

        await db.insert(coinTransactions).values({
            userId,
            type: 'earn',
            amount: bonus,
            description: 'Beri Peringkat 5 ⭐ di Google Play',
            balanceAfter: newBalance,
        });

        await db.insert(dailyRewards).values({
            userId,
            rewardType: 'rate_app',
            amount: bonus,
        });

        return c.json({ success: true, bonus, newBalance });
    } catch (error) {
        console.error('Claim rate error:', error);
        return c.json({ error: 'Failed to claim rate reward' }, 500);
    }
});

// POST /api/rewards/claim-ad — Reward for watching an ad
rewardsRoute.post('/claim-ad', async (c) => {
    try {
        const userId = c.get('user').id;
        const { type, amount } = await c.req.json();
        const now = new Date();
        const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        // Validate type
        if (!['checkin_bonus', 'general_ad'].includes(type)) {
            return c.json({ error: 'Invalid ad type' }, 400);
        }

        // Validate amount range
        if (type === 'checkin_bonus' && amount !== 20) {
            return c.json({ error: 'Invalid bonus amount' }, 400);
        }
        if (type === 'general_ad' && amount !== 10) {
            return c.json({ error: 'Invalid bonus amount' }, 400);
        }

        // Check daily limit for general ads (max 10/day)
        if (type === 'general_ad') {
            const todayAds = await db.select({ count: sql<number>`count(*)` }).from(dailyRewards)
                .where(and(
                    eq(dailyRewards.userId, userId),
                    eq(dailyRewards.rewardType, 'ad_general'),
                    gte(dailyRewards.claimedAt, todayStart),
                ));
            const adCount = todayAds[0]?.count || 0;
            if (adCount >= 10) {
                return c.json({ error: 'Daily ad limit reached', adsRemaining: 0 }, 400);
            }
        }

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        const newBalance = user.coins + amount;

        await db.update(users).set({ coins: newBalance, updatedAt: now }).where(eq(users.id, userId));

        const description = type === 'checkin_bonus'
            ? 'Bonus Cek Lainnya (Iklan)'
            : `Hadiah Tonton Iklan (+${amount})`;

        await db.insert(coinTransactions).values({
            userId,
            type: 'ad_reward',
            amount,
            description,
            balanceAfter: newBalance,
        });

        await db.insert(dailyRewards).values({
            userId,
            rewardType: type === 'checkin_bonus' ? 'ad_checkin' : 'ad_general',
            amount,
        });

        // Calculate remaining ads for general type
        let adsRemaining = 10;
        if (type === 'general_ad') {
            const todayAdsAfter = await db.select({ count: sql<number>`count(*)` }).from(dailyRewards)
                .where(and(
                    eq(dailyRewards.userId, userId),
                    eq(dailyRewards.rewardType, 'ad_general'),
                    gte(dailyRewards.claimedAt, todayStart),
                ));
            adsRemaining = Math.max(10 - (todayAdsAfter[0]?.count || 0), 0);
        }

        return c.json({ success: true, bonus: amount, newBalance, adsRemaining });
    } catch (error) {
        console.error('Claim ad error:', error);
        return c.json({ error: 'Failed to claim ad reward' }, 500);
    }
});

// GET /api/rewards/achievements
rewardsRoute.get('/achievements', async (c) => {
    try {
        const userId = c.get('user').id;
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const [allAchievements, userAchievementsList] = await Promise.all([
            db.select().from(achievements).where(eq(achievements.isActive, true)).orderBy(achievements.createdAt),
            db.select().from(userAchievements).where(eq(userAchievements.userId, userId)),
        ]);

        const unlockedIds = new Set(userAchievementsList.map(ua => ua.achievementId));

        const result = allAchievements.map(a => ({
            ...a,
            unlocked: unlockedIds.has(a.id),
            unlockedAt: userAchievementsList.find(ua => ua.achievementId === a.id)?.unlockedAt,
        }));

        return c.json(result);
    } catch (error) {
        console.error('Get achievements error:', error);
        return c.json({ error: 'Failed to get achievements' }, 500);
    }
});

// GET /api/rewards/transactions
rewardsRoute.get('/transactions', async (c) => {
    try {
        const userId = c.get('user').id;
        const page = parseInt(c.req.query('page') || '1');
        const limit = parseInt(c.req.query('limit') || '20');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const [transactions, totalResult] = await Promise.all([
            db.select().from(coinTransactions)
                .where(eq(coinTransactions.userId, userId))
                .orderBy(desc(coinTransactions.createdAt))
                .limit(limit)
                .offset((page - 1) * limit),
            db.select({ count: sql<number>`count(*)` }).from(coinTransactions)
                .where(eq(coinTransactions.userId, userId)),
        ]);

        return c.json({ transactions, total: totalResult[0]?.count || 0, page, limit });
    } catch (error) {
        console.error('Get transactions error:', error);
        return c.json({ error: 'Failed to get transactions' }, 500);
    }
});

export default rewardsRoute;
