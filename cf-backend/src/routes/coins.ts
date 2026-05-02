import { Hono } from 'hono';
import { eq, and, sql, gte } from 'drizzle-orm';
import { getDb } from '../db';
import { users, coinTransactions, dailyRewards } from '../db/schema';
import { Env, requireAuth } from '../middleware/auth';

const coinsRoute = new Hono<Env>();
coinsRoute.use('*', requireAuth);

const AD_REWARD = 20;
const MAX_ADS_PER_DAY = 10; // Tonton Iklan (Keuntungan Umum) = max 10/hari

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
        // WIB = UTC+7. Midnight WIB is 17:00 UTC of previous day.
        const wibNow = new Date(now.getTime() + 7 * 60 * 60 * 1000);
        const y = wibNow.getUTCFullYear();
        const m = wibNow.getUTCMonth();
        const d = wibNow.getUTCDate();
        const todayStart = new Date(Date.UTC(y, m, d) - 7 * 60 * 60 * 1000);
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        // Count today's ads by type
        const todayGeneralAds = await db.select({ count: sql<number>`count(*)` })
            .from(dailyRewards)
            .where(and(
                eq(dailyRewards.userId, userId),
                eq(dailyRewards.rewardType, 'ad_general'),
                gte(dailyRewards.claimedAt, todayStart),
            ));
        const todayCekLainnya = await db.select({ count: sql<number>`count(*)` })
            .from(dailyRewards)
            .where(and(
                eq(dailyRewards.userId, userId),
                eq(dailyRewards.rewardType, 'cek_lainnya'),
                gte(dailyRewards.claimedAt, todayStart),
            ));

        const generalCount = todayGeneralAds[0]?.count || 0;
        const cekLainnyaCount = todayCekLainnya[0]?.count || 0;

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
            adWatchCount: 0,
            adsRemaining: 0,
            cekLainnyaCount,
            cekLainnyaRemaining: Math.max(0, 15 - cekLainnyaCount),
            totalAdCount: cekLainnyaCount,
            totalAdsRemaining: Math.max(0, 15 - cekLainnyaCount),
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
// Supports 2 ad types:
//   type='general'  → Keuntungan Umum "Tonton" (max 10/day)
//   type='cek_lainnya' → Cek Lainnya after check-in (max 5/day)
coinsRoute.post('/watch-ad', async (c) => {
    try {
        const userId = c.get('user').id;
        const { type = 'general' } = await c.req.json();
        // WIB = UTC+7. Midnight WIB is 17:00 UTC of previous day.
        const wibNow = new Date(now.getTime() + 7 * 60 * 60 * 1000);
        const y = wibNow.getUTCFullYear();
        const m = wibNow.getUTCMonth();
        const d = wibNow.getUTCDate();
        const todayStart = new Date(Date.UTC(y, m, d) - 7 * 60 * 60 * 1000);
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const user = await db.select().from(users).where(eq(users.id, userId)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        // Determine reward config based on ad type
        const isCekLainnya = type === 'cek_lainnya';
        const rewardType = isCekLainnya ? 'cek_lainnya' : 'ad_general';
        const maxPerDay = isCekLainnya ? 15 : 0;
        if (!isCekLainnya) {
            return c.json({ error: 'Iklan umum sudah diganti dengan Cek Lainnya (Ad). Silakan gunakan tombol Cek Lainnya.' }, 400);
        }
        const rewardCoins = AD_REWARD; // 20

        // Check daily limit from dailyRewards table
        const todayAdsResult = await db.select({ count: sql<number>`count(*)` })
            .from(dailyRewards)
            .where(and(
                eq(dailyRewards.userId, userId),
                eq(dailyRewards.rewardType, rewardType),
                gte(dailyRewards.claimedAt, todayStart),
            ));
        const todayCount = todayAdsResult[0]?.count || 0;

        if (todayCount >= maxPerDay) {
            return c.json({ error: 'Daily ad limit reached', adsRemaining: 0, type }, 400);
        }

        // Atomic update: increment coins
        const newCount = todayCount + 1;
        await db.update(users).set({
            coins: sql`${users.coins} + ${rewardCoins}`,
            updatedAt: now,
        }).where(eq(users.id, userId));

        const updatedUser = await db.select({ coins: users.coins }).from(users).where(eq(users.id, userId)).limit(1).then(r => r[0]);
        const newBalance = updatedUser?.coins || (user.coins + rewardCoins);

        await db.insert(coinTransactions).values({
            userId,
            type: 'earn',
            amount: rewardCoins,
            description: isCekLainnya
                ? `Cek Lainnya (${newCount}/${maxPerDay})`
                : `Nonton Iklan (${newCount}/${maxPerDay})`,
            reference: `${rewardType}_${newCount}`,
        });

        await db.insert(dailyRewards).values({
            userId,
            rewardType,
            amount: rewardCoins,
        });

        return c.json({
            success: true,
            reward: rewardCoins,
            adCount: newCount,
            adsRemaining: maxPerDay - newCount,
            newBalance,
            type,
        });
    } catch (error) {
        console.error('Watch ad error:', error);
        return c.json({ error: 'Failed to reward ad watch' }, 500);
    }
});

// ── POST /api/coins/topup ───────────────────────────────────────────────────
coinsRoute.post('/topup', async (c) => {
    try {
        const user = c.get('user');
        const userId = user.id;
        const { packageId } = await c.req.json<{ packageId?: number }>();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        if (!packageId) {
            return c.json({ error: 'packageId diperlukan' }, 400);
        }

        // Cari paket
        const pkg = TOPUP_PACKAGES.find((p) => p.coins === packageId);
        if (!pkg) {
            return c.json({ error: 'Paket tidak valid', available: TOPUP_PACKAGES }, 400);
        }

        const orderId = `KU-${userId}-${Date.now()}`;
        const serverKey = c.env.MIDTRANS_SERVER_KEY;
        const isProduction = String(c.env.MIDTRANS_IS_PRODUCTION || '').toLowerCase() === 'true';

        console.log('[TOPUP DEBUG] Server Key exists:', !!serverKey, 'First 10 chars:', serverKey?.slice(0, 10));
        console.log('[TOPUP DEBUG] isProduction:', isProduction);

        const snapUrl = isProduction
            ? 'https://app.midtrans.com/snap/v1/transactions'
            : 'https://app.sandbox.midtrans.com/snap/v1/transactions';

        const authToken = Buffer.from(`${serverKey}:`).toString('base64');

        const requestBody = {
            transaction_details: {
                order_id: orderId,
                gross_amount: pkg.price,
            },
            customer_details: {
                first_name: user.name || 'User',
                email: user.email || '',
                phone: '',
            },
            credit_card: {
                secure: true,
            },
        };

        console.log('[TOPUP DEBUG] Request body:', JSON.stringify(requestBody));

        const snapRes = await fetch(snapUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Basic ${authToken}`,
            },
            body: JSON.stringify(requestBody),
        });

        console.log('[TOPUP DEBUG] Midtrans response status:', snapRes.status);

        if (!snapRes.ok) {
            const errBody = await snapRes.text().catch(() => 'Unknown error');
            console.error('Midtrans error:', snapRes.status, errBody);
            return c.json({ error: 'Gagal membuat transaksi Midtrans', detail: errBody }, 502);
        }

        const snapData: any = await snapRes.json();

        // Simpan transaksi pending
        await db.insert(coinTransactions).values({
            userId,
            type: 'topup_pending',
            amount: pkg.coins,
            description: `Top Up ${pkg.label} - ${orderId}`,
            reference: orderId,
        });

        return c.json({
            success: true,
            orderId,
            snapToken: snapData.token,
            redirectUrl: snapData.redirect_url,
            package: {
                coins: pkg.coins,
                price: pkg.price,
            },
        });
    } catch (error: any) {
        console.error('Topup error:', error);
        return c.json({ error: 'Gagal memproses top up', message: error?.message || String(error) }, 500);
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

        // Deduct coins atomically + set VIP status
        await db.update(users).set({
            coins: sql`${users.coins} - ${pkg.coins}`,
            adFreeExpiry: newExpiry,
            vipStatus: true,
            vipExpiry: newExpiry,
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

// ── POST /api/coins/fix-vip-status ────────────────────────────────────────────
// Fix single user VIP status manually (for users affected by old bug)
coinsRoute.post('/fix-vip-status', async (c) => {
    try {
        const { email } = await c.req.json();
        if (!email) return c.json({ error: 'Email diperlukan' }, 400);

        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const user = await db.select().from(users).where(eq(users.email, email)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User tidak ditemukan' }, 404);

        const now = new Date();
        const hasActiveAdFree = user.adFreeExpiry && new Date(user.adFreeExpiry) > now;
        const alreadyVip = user.vipStatus === true;

        let patched = false;
        if (hasActiveAdFree && !alreadyVip) {
            await db.update(users).set({
                vipStatus: true,
                vipExpiry: user.adFreeExpiry,
                updatedAt: now,
            }).where(eq(users.id, user.id));
            patched = true;
        }

        return c.json({
            success: true,
            patched,
            email: user.email,
            name: user.name,
            before: {
                vipStatus: user.vipStatus,
                vipExpiry: user.vipExpiry,
                adFreeExpiry: user.adFreeExpiry,
            },
            after: patched ? {
                vipStatus: true,
                vipExpiry: user.adFreeExpiry,
            } : null,
            message: patched
                ? `VIP status berhasil diperbaiki untuk ${email}`
                : `Tidak perlu patch: ${alreadyVip ? 'sudah VIP' : 'tidak punya adFree aktif'}`,
        });
    } catch (error: any) {
        console.error('Fix VIP status error:', error);
        return c.json({ error: 'Gagal memperbaiki VIP status', message: error?.message }, 500);
    }
});

// ── POST /api/coins/migrate-vip ───────────────────────────────────────────────
// Mass-migrate all users with active adFreeExpiry but vipStatus=false
coinsRoute.post('/migrate-vip', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const now = new Date();

        // Find all users with active adFree but vipStatus=false
        const affectedUsers = await db.select({
            id: users.id,
            email: users.email,
            name: users.name,
            adFreeExpiry: users.adFreeExpiry,
            vipStatus: users.vipStatus,
        }).from(users).where(
            sql`${users.adFreeExpiry} IS NOT NULL AND ${users.adFreeExpiry} > ${now} AND (${users.vipStatus} = false OR ${users.vipStatus} IS NULL)`
        );

        let fixedCount = 0;
        for (const u of affectedUsers) {
            await db.update(users).set({
                vipStatus: true,
                vipExpiry: u.adFreeExpiry,
                updatedAt: now,
            }).where(eq(users.id, u.id));
            fixedCount++;
        }

        return c.json({
            success: true,
            affectedCount: affectedUsers.length,
            fixedCount,
            users: affectedUsers.map(u => ({ email: u.email, name: u.name, adFreeExpiry: u.adFreeExpiry })),
            message: `${fixedCount} user berhasil dimigrasi ke VIP status`,
        });
    } catch (error: any) {
        console.error('Migrate VIP error:', error);
        return c.json({ error: 'Gagal migrasi VIP', message: error?.message }, 500);
    }
});

export default coinsRoute;
