import { Hono } from 'hono';
import { eq, and, sql, gte } from 'drizzle-orm';
import { getDb } from '../db';
import { users, coinTransactions, dailyRewards } from '../db/schema';
import { Env, requireAuth } from '../middleware/auth';

const coinsRoute = new Hono<Env>();
coinsRoute.use('*', requireAuth);

const AD_REWARD = 20;
const MAX_ADS_PER_DAY = 15;

const AD_FREE_PACKAGES = [
    { hours: 1,  coins: 1000,  label: 'Bebas Iklan 1 Jam' },
    { hours: 4,  coins: 3000,  label: 'Bebas Iklan 4 Jam' },
    { hours: 24, coins: 10000, label: 'Bebas Iklan 24 Jam' },
];

const TOPUP_PACKAGES = [
    { coins: 2000,  price: 5000,  label: '2.000 Koin' },
    { coins: 5000,  price: 10000, label: '5.000 Koin' },
    { coins: 12000, price: 20000, label: '12.000 Koin' },
];

function toWIBDateString(date: Date): string {
    const wib = new Date(date.getTime() + 7 * 60 * 60 * 1000);
    return wib.toISOString().slice(0, 10);
}

function isSameDay(date1: Date, date2: Date): boolean {
    return toWIBDateString(date1) === toWIBDateString(date2);
}

// ── GET /api/coins/status ────────────────────────────────────────────────────
coinsRoute.get('/status', async (c) => {
    try {
        const userId = c.get('user').id;
        const now = new Date();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        // Ad watch count today
        let adWatchCount = 0;
        if (user.adWatchDate && isSameDay(new Date(user.adWatchDate), now)) {
            adWatchCount = user.adWatchCount || 0;
        }

        // Ad-free time remaining
        let adFreeRemaining = 0;
        if (user.adFreeExpiry && new Date(user.adFreeExpiry) > now) {
            adFreeRemaining = Math.max(0, Math.floor((new Date(user.adFreeExpiry).getTime() - now.getTime()) / 1000));
        }

        // VIP time remaining (for reference)
        let vipRemaining = 0;
        if (user.vipExpiry && new Date(user.vipExpiry) > now) {
            vipRemaining = Math.max(0, Math.floor((new Date(user.vipExpiry).getTime() - now.getTime()) / 1000));
        }

        return c.json({
            coins: user.coins,
            purchasedCoins: user.purchasedCoins || 0,
            adWatchCount,
            adsRemaining: Math.max(0, MAX_ADS_PER_DAY - adWatchCount),
            adFreeRemaining,
            vipRemaining,
            adFreePackages: AD_FREE_PACKAGES,
            topupPackages: TOPUP_PACKAGES,
        });
    } catch (error) {
        console.error('Coins status error:', error);
        return c.json({ error: 'Failed to get coins status' }, 500);
    }
});

// ── POST /api/coins/watch-ad ────────────────────────────────────────────────
coinsRoute.post('/watch-ad', async (c) => {
    try {
        const userId = c.get('user').id;
        const now = new Date();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        // Check daily limit
        let todayCount = 0;
        if (user.adWatchDate && isSameDay(new Date(user.adWatchDate), now)) {
            todayCount = user.adWatchCount || 0;
        }

        if (todayCount >= MAX_ADS_PER_DAY) {
            return c.json({ error: 'Daily ad limit reached', adsRemaining: 0 }, 400);
        }

        // Atomic update: increment coins and ad count
        const newCount = todayCount + 1;
        await db.update(users).set({
            coins: sql`${users.coins} + ${AD_REWARD}`,
            adWatchCount: newCount,
            adWatchDate: now,
            updatedAt: now,
        }).where(eq(users.id, userId));

        const updatedUser = await db.select({ coins: users.coins }).from(users).where(eq(users.id, userId)).limit(1).then(r => r[0]);
        const newBalance = updatedUser?.coins || (user.coins + AD_REWARD);

        await db.insert(coinTransactions).values({
            userId,
            type: 'earn',
            amount: AD_REWARD,
            description: `Nonton Iklan (${newCount}/${MAX_ADS_PER_DAY})`,
            reference: `ad_watch_${newCount}`,
        });

        return c.json({
            success: true,
            reward: AD_REWARD,
            adCount: newCount,
            adsRemaining: MAX_ADS_PER_DAY - newCount,
            newBalance,
        });
    } catch (error) {
        console.error('Watch ad error:', error);
        return c.json({ error: 'Failed to reward ad watch' }, 500);
    }
});

// ── POST /api/coins/topup ───────────────────────────────────────────────────
coinsRoute.post('/topup', async (c) => {
    try {
        const userId = c.get('user').id;
        const { packageId } = await c.req.json();
        const now = new Date();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const pkg = TOPUP_PACKAGES.find(p => p.coins === packageId || p.label === packageId);
        if (!pkg) {
            return c.json({ error: 'Invalid package', available: TOPUP_PACKAGES }, 400);
        }

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        // In production, this should integrate with payment gateway (Midtrans/Xendit)
        // For now, we create a pending transaction record
        const transactionId = `topup_${Date.now()}_${userId.slice(0, 8)}`;

        await db.insert(coinTransactions).values({
            userId,
            type: 'topup',
            amount: pkg.coins,
            description: `Top Up ${pkg.label} - Rp ${pkg.price.toLocaleString('id-ID')}`,
            reference: transactionId,
        });

        // NOTE: In real implementation, coins are added AFTER payment confirmation
        // For testing/demo, we add immediately
        await db.update(users).set({
            coins: sql`${users.coins} + ${pkg.coins}`,
            purchasedCoins: sql`${users.purchasedCoins} + ${pkg.coins}`,
            updatedAt: now,
        }).where(eq(users.id, userId));

        const updatedUser = await db.select({ coins: users.coins, purchasedCoins: users.purchasedCoins }).from(users).where(eq(users.id, userId)).limit(1).then(r => r[0]);

        return c.json({
            success: true,
            transactionId,
            package: pkg,
            newBalance: updatedUser?.coins,
            purchasedCoins: updatedUser?.purchasedCoins,
            message: 'Top up berhasil! (Demo mode - payment gateway belum terintegrasi)',
        });
    } catch (error) {
        console.error('Topup error:', error);
        return c.json({ error: 'Failed to process top up' }, 500);
    }
});

// ── POST /api/coins/redeem-ad-free ────────────────────────────────────────────
coinsRoute.post('/redeem-ad-free', async (c) => {
    try {
        const userId = c.get('user').id;
        const { hours } = await c.req.json();
        const now = new Date();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const pkg = AD_FREE_PACKAGES.find(p => p.hours === hours);
        if (!pkg) {
            return c.json({ error: 'Invalid package', available: AD_FREE_PACKAGES }, 400);
        }

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        if (user.coins < pkg.coins) {
            return c.json({
                error: 'Koin tidak cukup',
                required: pkg.coins,
                current: user.coins,
                shortfall: pkg.coins - user.coins,
            }, 400);
        }

        // Calculate new expiry (extend if already has active ad-free)
        let newExpiry = new Date(now.getTime() + hours * 60 * 60 * 1000);
        if (user.adFreeExpiry && new Date(user.adFreeExpiry) > now) {
            // Extend from existing expiry
            newExpiry = new Date(new Date(user.adFreeExpiry).getTime() + hours * 60 * 60 * 1000);
        }

        // Deduct coins atomically
        await db.update(users).set({
            coins: sql`${users.coins} - ${pkg.coins}`,
            adFreeExpiry: newExpiry,
            updatedAt: now,
        }).where(eq(users.id, userId));

        const updatedUser = await db.select({ coins: users.coins }).from(users).where(eq(users.id, userId)).limit(1).then(r => r[0]);

        await db.insert(coinTransactions).values({
            userId,
            type: 'spend',
            amount: -pkg.coins,
            description: pkg.label,
            reference: `ad_free_${hours}h`,
        });

        const totalSeconds = Math.floor((newExpiry.getTime() - now.getTime()) / 1000);
        const totalHours = Math.floor(totalSeconds / 3600);

        return c.json({
            success: true,
            package: pkg,
            newBalance: updatedUser?.coins,
            adFreeUntil: newExpiry.toISOString(),
            adFreeRemainingSeconds: totalSeconds,
            adFreeRemainingHours: totalHours,
            message: `Bebas iklan diperpanjang hingga ${newExpiry.toLocaleString('id-ID', { timeZone: 'Asia/Jakarta' })}`,
        });
    } catch (error) {
        console.error('Redeem ad-free error:', error);
        return c.json({ error: 'Failed to redeem ad-free' }, 500);
    }
});

export default coinsRoute;
