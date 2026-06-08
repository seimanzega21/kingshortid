import { Hono } from 'hono';
import { eq, and, sql, desc, gte } from 'drizzle-orm';
import { getDb } from '../db';
import { users, coinTransactions, dailyRewards, watchHistory, achievements, userAchievements } from '../db/schema';
import { Env, requireAuth } from '../middleware/auth';
import { watchVideoHandler, redeemVipHandler } from './coins';

const rewardsRoute = new Hono<Env>();
rewardsRoute.use('*', requireAuth);

const STREAK_BONUSES = [
    { day: 1, coins: 50 },
    { day: 2, coins: 50 },
    { day: 3, coins: 50 },
    { day: 4, coins: 50 },
    { day: 5, coins: 50 },
    { day: 6, coins: 50 },
    { day: 7, coins: 200 }, // Base 200, will be randomized 200-500 at runtime
];

// Coin milestones: target → bonus reward
const COIN_MILESTONES = [
    { target: 500, bonus: 50, label: 'Milestone pertama!' },
    { target: 1000, bonus: 100, label: 'Kolektor koin!' },
    { target: 2000, bonus: 200, label: 'Master koin!' },
    { target: 5000, bonus: 500, label: 'Raja koin!' },
];

function toWIBDateString(date: Date): string {
    const d = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
    if (isNaN(d.getTime())) return '';
    return new Intl.DateTimeFormat('en-CA', {
        timeZone: 'Asia/Jakarta',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    }).format(d);
}

function isSameDay(date1: Date, date2: Date): boolean {
    return toWIBDateString(date1) === toWIBDateString(date2);
}

// POST /api/rewards/claim-daily
rewardsRoute.post('/claim-daily', async (c) => {
    try {
        const userId = c.get('user').id;
        const now = new Date();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        if (user.lastCheckIn && isSameDay(new Date(user.lastCheckIn), now)) {
            return c.json({ error: 'Already checked in today', streak: user.checkInStreak }, 400);
        }

        const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        const yesterdayDateStr = toWIBDateString(yesterday);
        const lastCheckInDateStr = user.lastCheckIn ? toWIBDateString(new Date(user.lastCheckIn)) : null;

        let newStreak: number;
        if (lastCheckInDateStr === yesterdayDateStr) {
            if (user.checkInStreak === 7) {
                // Completed 7-day cycle, start new cycle as day 1
                newStreak = 1;
            } else {
                newStreak = (user.checkInStreak || 0) + 1;
            }
        } else if (user.lastCheckIn && isSameDay(new Date(user.lastCheckIn), now)) {
            return c.json({ error: 'Already checked in today', streak: user.checkInStreak }, 400);
        } else {
            // Bolong absen — RESET streak to day 1
            newStreak = 1;
        }

        // Hitung bonus koin
        let bonusCoins = STREAK_BONUSES.find(b => b.day === newStreak)?.coins || 50;
        
        // Hari 7: random 200-500 koin (default 200)
        if (newStreak === 7) {
            bonusCoins = Math.floor(Math.random() * 301) + 200; // 200-500
        }

        await db.update(users).set({
            coins: sql`${users.coins} + ${bonusCoins}`,
            lastCheckIn: now,
            checkInStreak: newStreak,
            updatedAt: now,
        }).where(eq(users.id, userId));

        const updatedUser = await db.select({ coins: users.coins }).from(users).where(eq(users.id, userId)).limit(1).then(r => r[0]);
        const newBalance = updatedUser?.coins || user.coins + bonusCoins;

        await db.insert(coinTransactions).values({
            userId,
            type: 'bonus',
            amount: bonusCoins,
            description: `Check-In Hari ke-${newStreak}`,
        });

        await db.insert(dailyRewards).values({
            userId,
            rewardType: 'check_in',
            amount: bonusCoins,
        });

        return c.json({
            success: true,
            streak: newStreak,
            coins: bonusCoins,
            newBalance,
        });
    } catch (error) {
        console.error('Check-in error:', error);
        return c.json({ error: 'Failed to check in' }, 500);
    }
});

// Deprecated endpoint alias
rewardsRoute.post('/check-in', async (c) => {
    return c.redirect('/api/rewards/claim-daily', 307);
});


// GET /api/rewards/status
rewardsRoute.get('/status', async (c) => {
    try {
        const userId = c.get('user').id;
        const now = new Date();
        
        // WIB = UTC+7. Midnight WIB is 17:00 UTC of previous day.
        const wibNow = new Date(now.getTime() + 7 * 60 * 60 * 1000);
        const y = wibNow.getUTCFullYear();
        const m = wibNow.getUTCMonth();
        const d = wibNow.getUTCDate();
        const todayStart = new Date(Date.UTC(y, m, d) - 7 * 60 * 60 * 1000);
        
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        const hasClaimedToday = user.lastCheckIn && isSameDay(new Date(user.lastCheckIn), now);

        const streak = user.checkInStreak || 0;

        const dailyEpisodesResult = await db.select({ count: sql<number>`count(*)` }).from(watchHistory)
            .where(and(eq(watchHistory.userId, userId), gte(watchHistory.watchedAt, todayStart)));
        const watchCount = Number(dailyEpisodesResult[0]?.count || 0);

        const claimedDailyRewardsResult = await db.select().from(dailyRewards)
            .where(and(
                eq(dailyRewards.userId, userId),
                sql`${dailyRewards.rewardType} LIKE 'watch_%'`,
                gte(dailyRewards.claimedAt, todayStart),
            ));
        const claimedWatchRewards = claimedDailyRewardsResult.map(r => r.rewardType.replace('watch_', ''));

        // Check if user has rated the app (lifetime)
        const rateAppClaim = await db.select().from(dailyRewards)
            .where(and(eq(dailyRewards.userId, userId), eq(dailyRewards.rewardType, 'rate_app')))
            .limit(1).then((r: any[]) => r[0]);
        const hasRated = !!rateAppClaim;

        // Ad Stats (Keuntungan Umum & Cek Lainnya)
        const todayGeneralAds = await db.select({ count: sql<number>`count(*)` }).from(dailyRewards)
            .where(and(eq(dailyRewards.userId, userId), eq(dailyRewards.rewardType, 'ad_general'), gte(dailyRewards.claimedAt, todayStart)));
        const todayCekLainnya = await db.select({ count: sql<number>`count(*)` }).from(dailyRewards)
            .where(and(eq(dailyRewards.userId, userId), eq(dailyRewards.rewardType, 'cek_lainnya'), gte(dailyRewards.claimedAt, todayStart)));

        const adCount = Number(todayGeneralAds[0]?.count || 0);
        const cekLainnyaCount = Number(todayCekLainnya[0]?.count || 0);

        // Check claimed milestones (lifetime)
        const milestoneResults = await db.select().from(dailyRewards)
            .where(and(
                eq(dailyRewards.userId, userId),
                sql`${dailyRewards.rewardType} LIKE 'milestone_%'`,
            ));
        const claimedMilestones = milestoneResults.map(r => parseInt(r.rewardType.replace('milestone_', '')));

        // Calculate claimed days based on CURRENT streak (sequential absolute)
        const claimedDays = (() => {
            if (streak === 0) return [];
            if (!hasClaimedToday) {
                // Check if last claim was yesterday; if not, user missed = reset
                const lastCheckIn = user.lastCheckIn ? new Date(user.lastCheckIn) : null;
                const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                if (lastCheckIn && !isSameDay(lastCheckIn, yesterday)) {
                    return []; // Missed a day = all uncheck
                }
                return Array.from({ length: Math.min(streak, 7) }, (_, i) => i + 1);
            }
            return Array.from({ length: Math.min(streak, 7) }, (_, i) => i + 1);
        })();

        // Compute displayStreak: 0 if missed or cycle complete
        const displayStreak = (() => {
            if (streak === 0) return 0;
            if (!hasClaimedToday) {
                const lastCheckIn = user.lastCheckIn ? new Date(user.lastCheckIn) : null;
                const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                if (lastCheckIn && !isSameDay(lastCheckIn, yesterday)) {
                    return 0; // Missed
                }
            }
            return streak;
        })();

        const totalCoins = (user.coins || 0) + (user.purchasedCoins || 0);

        return c.json({
            coins: user.coins,
            purchasedCoins: user.purchasedCoins || 0,
            totalCoins,
            hasClaimedToday,
            streak: displayStreak,
            claimedDays,
            watchCount,
            claimedWatchRewards,
            hasRated,
            claimedMilestones,
            adCount,
            adsRemaining: Math.max(0, 10 - adCount),
            cekLainnyaCount,
            cekLainnyaRemaining: Math.max(0, 15 - cekLainnyaCount),
            vipExpiry: user.vipExpiry
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
        const watchedCount = Number(watchedResult[0]?.count || 0);

        if (watchedCount < task.target) {
            return c.json({ error: `Need ${task.target} episodes, watched ${watchedCount}` }, 400);
        }

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        // Use atomic increment
        await db.update(users).set({ 
            coins: sql`${users.coins} + ${task.bonus}`, 
            updatedAt: now 
        }).where(eq(users.id, userId));

        // Fetch new balance
        const updatedUser = await db.select({ coins: users.coins }).from(users).where(eq(users.id, userId)).limit(1).then(r => r[0]);
        const newBalance = updatedUser?.coins || user.coins + task.bonus;

        await db.insert(coinTransactions).values({
            userId,
            type: 'earn',
            amount: task.bonus,
            description: `Hadiah Menonton: ${task.target} episode`,
            // balanceAfter: newBalance,
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
        await db.update(users).set({ 
            coins: sql`${users.coins} + ${bonus}`, 
            updatedAt: now 
        }).where(eq(users.id, userId));

        const updatedUser = await db.select({ coins: users.coins }).from(users).where(eq(users.id, userId)).limit(1).then(r => r[0]);
        const newBalance = updatedUser?.coins || user.coins + bonus;

        await db.insert(coinTransactions).values({
            userId,
            type: 'earn',
            amount: bonus,
            description: 'Beri Peringkat 5 ⭐ di Google Play',
            // balanceAfter: newBalance,
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

// POST /api/rewards/earn-bonus-video — Reward for watching an ad
const earnBonusVideoHandler = async (c: any) => {
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
        if (type === 'checkin_bonus' && amount !== 50) {
            return c.json({ error: 'Invalid bonus amount' }, 400);
        }
        if (type === 'general_ad' && amount !== 50) {
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
            const adCount = Number(todayAds[0]?.count || 0);
            if (adCount >= 10) {
                return c.json({ error: 'Daily ad limit reached', adsRemaining: 0 }, 400);
            }
        }

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        // Use atomic increment
        await db.update(users).set({ 
            coins: sql`${users.coins} + ${amount}`, 
            updatedAt: now 
        }).where(eq(users.id, userId));

        const updatedUser = await db.select({ coins: users.coins }).from(users).where(eq(users.id, userId)).limit(1).then(r => r[0]);
        const newBalance = updatedUser?.coins || user.coins + amount;

        const description = type === 'checkin_bonus'
            ? 'Bonus Cek Lainnya (Iklan)'
            : `Hadiah Tonton Iklan (+${amount})`;

        await db.insert(coinTransactions).values({
            userId,
            type: 'earn', // Changed from ad_reward to match other working endpoints
            amount,
            description,
            // balanceAfter: newBalance,
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
            adsRemaining = Math.max(10 - Number(todayAdsAfter[0]?.count || 0), 0);
        }

        return c.json({ success: true, bonus: amount, newBalance, adsRemaining });
    } catch (error) {
        console.error('Claim ad error:', error);
        return c.json({ error: 'Failed to claim ad reward' }, 500);
    }
};

rewardsRoute.post('/complete-task', earnBonusVideoHandler);
// Keep old routes for backward compatibility with old APKs
rewardsRoute.post('/earn-bonus-video', earnBonusVideoHandler);
rewardsRoute.post('/claim-ad', earnBonusVideoHandler);

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

        console.log('DEBUG TRANSACTIONS LENGTH:', transactions.length);
        console.log('DEBUG TRANSACTIONS LIMIT/PAGE:', limit, page, 'USER_ID:', userId);
        return c.json({ transactions, total: Number(totalResult[0]?.count || 0), page, limit });
    } catch (error) {
        console.error('Get transactions error:', error);
        return c.json({ error: 'Failed to get transactions' }, 500);
    }
});

// POST /api/rewards/claim-milestone — One-time reward for reaching coin milestones
rewardsRoute.post('/claim-milestone', async (c) => {
    try {
        const userId = c.get('user').id;
        const { target } = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        // Validate milestone target
        const milestone = COIN_MILESTONES.find(m => m.target === target);
        if (!milestone) return c.json({ error: 'Invalid milestone target' }, 400);

        // Check if already claimed
        const existingClaim = await db.select().from(dailyRewards)
            .where(and(
                eq(dailyRewards.userId, userId),
                eq(dailyRewards.rewardType, `milestone_${target}`),
            ))
            .limit(1).then((r: any[]) => r[0]);

        if (existingClaim) return c.json({ error: 'Milestone already claimed' }, 400);

        // Check if user has enough coins
        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        if (user.coins < target) {
            return c.json({ error: `Need ${target} coins, have ${user.coins}` }, 400);
        }

        const newBalance = user.coins + milestone.bonus;

        let vipUpdate = {};
        let vipMessage = '';
        if (target === 5000) {
            const now = new Date();
            let currentExpiry = user.vipExpiry ? new Date(user.vipExpiry) : now;
            if (currentExpiry.getTime() < now.getTime()) {
                currentExpiry = now; 
            }
            // Add 24 hours VIP
            const newExpiry = new Date(currentExpiry.getTime() + 24 * 60 * 60 * 1000); 
            vipUpdate = { vipExpiry: newExpiry, vipStatus: true };
            vipMessage = ' + VIP 24 Jam Gratis';
        }

        // Use atomic increment
        await db.update(users).set({ 
            coins: sql`${users.coins} + ${milestone.bonus}`, 
            updatedAt: new Date(), 
            ...vipUpdate 
        }).where(eq(users.id, userId));

        const updatedUser = await db.select({ coins: users.coins }).from(users).where(eq(users.id, userId)).limit(1).then(r => r[0]);
        const finalBalance = updatedUser?.coins || user.coins + milestone.bonus;

        await db.insert(coinTransactions).values({
            userId,
            type: 'bonus',
            amount: milestone.bonus,
            description: `🎉 Milestone ${target} koin — ${milestone.label}${vipMessage}`,
            // balanceAfter: newBalance,
        });

        await db.insert(dailyRewards).values({
            userId,
            rewardType: `milestone_${target}`,
            amount: milestone.bonus,
        });

        return c.json({ success: true, bonus: milestone.bonus, newBalance, label: milestone.label });
    } catch (error) {
        console.error('Claim milestone error:', error);
        return c.json({ error: 'Failed to claim milestone' }, 500);
    }
});
// POST /api/rewards/exchange-vip
rewardsRoute.post('/exchange-vip', async (c) => {
    try {
        const userId = c.get('user').id;
        const now = new Date();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        if (user.coins < 2000) {
            return c.json({ error: 'Koin tidak cukup' }, 400);
        }

        const newBalance = user.coins - 2000;
        
        let currentExpiry = user.vipExpiry ? new Date(user.vipExpiry) : now;
        if (currentExpiry.getTime() < now.getTime()) {
            currentExpiry = now; 
        }
        
        const newExpiry = new Date(currentExpiry.getTime() + 60 * 60 * 1000); 
        
        await db.update(users).set({ 
            coins: newBalance, 
            vipStatus: true,
            vipExpiry: newExpiry,
            updatedAt: now 
        }).where(eq(users.id, userId));

        await db.insert(coinTransactions).values({
            userId,
            type: 'spend',
            amount: -2000,
            description: 'Tukar Koin: VIP Bebas Iklan (1 Jam)',
        });

        return c.json({ success: true, newBalance, vipExpiry: newExpiry, vipStatus: true });
    } catch (error) {
        console.error('Exchange VIP error:', error);
        return c.json({ error: 'Failed to exchange VIP' }, 500);
    }
});

rewardsRoute.post('/watch-video', watchVideoHandler);
rewardsRoute.post('/redeem-vip', redeemVipHandler);

rewardsRoute.get('/history', async (c) => {
    try {
        const userId = c.get('user').id;
        const page = parseInt(c.req.query('page') || '1');
        const limit = parseInt(c.req.query('limit') || '50');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const items = await db.select()
            .from(coinTransactions)
            .where(eq(coinTransactions.userId, userId))
            .orderBy(desc(coinTransactions.createdAt))
            .limit(limit)
            .offset((page - 1) * limit);

        return c.json({
            data: items.map(item => ({
                id: item.id,
                type: item.type,
                amount: item.amount,
                description: item.description,
                reference: item.reference,
                balanceAfter: item.balanceAfter,
                createdAt: item.createdAt,
            })),
            page,
            limit,
        });
    } catch (error) {
        console.error('Get rewards history error:', error);
        return c.json({ error: 'Failed to get rewards history' }, 500);
    }
});

export default rewardsRoute;
