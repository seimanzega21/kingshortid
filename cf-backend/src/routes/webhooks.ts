import { Hono } from 'hono';
import { eq, sql } from 'drizzle-orm';
import { getDb } from '../db';
import { users, coinTransactions } from '../db/schema';
import type { Env } from '../middleware/auth';

const webhooksRoute = new Hono<Env>();

const PLAN_DAYS: Record<string, number> = {
    'kingshort_weekly': 7,
    'kingshort_monthly': 30,
};

const COIN_PACKAGES: Record<string, { base: number; bonus: number }> = {
    'kingshort_2000_coins': { base: 2000, bonus: 100 },
    'kingshort_5000_coins': { base: 5000, bonus: 800 },
    'kingshort_12000_coins': { base: 12000, bonus: 0 },
    'coins_2000': { base: 2000, bonus: 100 },
    'coins_5000': { base: 5000, bonus: 800 },
    'coins_12000': { base: 12000, bonus: 0 },
};

// POST /api/webhooks/revenuecat
webhooksRoute.post('/revenuecat', async (c) => {
    // Validate authorization header
    const authHeader = c.req.header('Authorization');
    const expectedSecret = c.env.REVENUECAT_WEBHOOK_SECRET;

    if (!authHeader || authHeader !== expectedSecret) {
        console.warn('RevenueCat webhook: unauthorized request');
        return c.json({ error: 'Unauthorized' }, 401);
    }

    let body: any;
    try {
        body = await c.req.json();
    } catch {
        return c.json({ error: 'Invalid JSON' }, 400);
    }

    const { event } = body;
    if (!event) return c.json({ ok: true });

    const { type, app_user_id, product_id, expiration_at_ms } = event;
    console.log(`RevenueCat webhook: type=${type}, user=${app_user_id}, product=${product_id}`);

    const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

    try {
        switch (type) {
            case 'INITIAL_PURCHASE':
            case 'RENEWAL':
            case 'UNCANCELLATION': {
                // Determine expiry date
                let expiry: Date;
                if (expiration_at_ms) {
                    expiry = new Date(expiration_at_ms);
                } else {
                    const days = PLAN_DAYS[product_id] ?? 7;
                    expiry = new Date(Date.now() + days * 24 * 60 * 60 * 1000);
                }

                await db.update(users)
                    .set({
                        vipStatus: true,
                        vipExpiry: expiry,
                        updatedAt: new Date(),
                    })
                    .where(eq(users.id, app_user_id));

                console.log(`Activated subscription for user ${app_user_id} until ${expiry.toISOString()}`);
                break;
            }

            case 'CANCELLATION':
            case 'EXPIRATION':
            case 'BILLING_ISSUE': {
                await db.update(users)
                    .set({
                        vipStatus: false,
                        updatedAt: new Date(),
                    })
                    .where(eq(users.id, app_user_id));

                console.log(`Deactivated subscription for user ${app_user_id}`);
                break;
            }

            case 'NON_SUBSCRIPTION_PURCHASE': {
                const transactionId = event.transaction_id || event.id;

                // 1. Prevent duplicate processing
                const existingTx = await db.select()
                    .from(coinTransactions)
                    .where(eq(coinTransactions.reference, transactionId))
                    .limit(1)
                    .then((r: any[]) => r[0]);

                if (existingTx) {
                    console.log(`RevenueCat webhook: transaction ${transactionId} already processed.`);
                    break;
                }

                // 2. Map package base + bonus
                let packageInfo = COIN_PACKAGES[product_id];
                if (!packageInfo) {
                    // Fallback: parse number from product_id
                    const match = product_id.match(/\d+/);
                    if (match) {
                        packageInfo = { base: parseInt(match[0]), bonus: 0 };
                    }
                }

                if (!packageInfo) {
                    console.error(`RevenueCat webhook: could not determine coin amount for product ${product_id}`);
                    break;
                }

                const { base: baseCoins, bonus: bonusCoins } = packageInfo;
                const totalAdded = baseCoins + bonusCoins;

                // 3. Increment purchasedCoins (paid) and coins (bonus)
                await db.update(users)
                    .set({
                        purchasedCoins: sql`${users.purchasedCoins} + ${baseCoins}`,
                        coins: sql`${users.coins} + ${bonusCoins}`,
                        updatedAt: new Date(),
                    })
                    .where(eq(users.id, app_user_id));

                // 4. Retrieve new total balance for transaction log
                const updatedUser = await db.select({
                    coins: users.coins,
                    purchasedCoins: users.purchasedCoins
                }).from(users).where(eq(users.id, app_user_id)).limit(1).then(r => r[0]);

                const totalBalanceAfter = (updatedUser?.coins || 0) + (updatedUser?.purchasedCoins || 0);

                // 5. Log transaction
                await db.insert(coinTransactions).values({
                    userId: app_user_id,
                    type: 'topup',
                    amount: totalAdded,
                    description: `Top Up Success (RevenueCat: ${product_id}, Base: ${baseCoins}, Bonus: ${bonusCoins})`,
                    reference: transactionId,
                    balanceAfter: totalBalanceAfter,
                });

                console.log(`RevenueCat webhook: credited ${baseCoins} purchased + ${bonusCoins} bonus coins to user ${app_user_id}`);
                break;
            }

            default:
                console.log(`RevenueCat webhook: unhandled event type ${type}`);
        }
    } catch (err) {
        console.error('RevenueCat webhook DB error:', err);
        return c.json({ error: 'DB error' }, 500);
    }

    return c.json({ ok: true });
});

async function calculateSHA512(str: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(str);
    const hashBuffer = await crypto.subtle.digest('SHA-512', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// POST /api/webhooks/midtrans
// Called by Midtrans when a Top Up payment completes
webhooksRoute.post('/midtrans', async (c) => {
    try {
        let body: any;
        try {
            body = await c.req.json();
        } catch {
            return c.json({ ok: true });
        }

        const { order_id, transaction_status, gross_amount, status_code, signature_key } = body;
        console.log(`Midtrans webhook: order_id=${order_id}, status=${transaction_status}`);

        const serverKey = c.env.MIDTRANS_SERVER_KEY;
        if (!serverKey) {
            console.error('MIDTRANS_SERVER_KEY is not defined in environment');
            return c.json({ error: 'Server configuration error' }, 500);
        }

        const payloadToSign = `${order_id}${status_code}${gross_amount}${serverKey}`;
        const calculatedSignature = await calculateSHA512(payloadToSign);

        if (calculatedSignature !== signature_key) {
            console.warn(`Midtrans webhook: signature verification failed. Calculated=${calculatedSignature}, Got=${signature_key}`);
            return c.json({ error: 'Invalid signature key' }, 403);
        }

        // Only process successful payments
        const successStatuses = ['capture', 'settlement'];
        const pendingStatuses = ['pending', 'authorize'];
        const failedStatuses = ['deny', 'cancel', 'expire', 'failure'];

        if (!order_id || !order_id.toString().startsWith('KU-')) {
            return c.json({ ok: true });
        }

        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        // Find the transaction
        const tx = await db.select()
            .from(coinTransactions)
            .where(eq(coinTransactions.reference, order_id.toString()))
            .limit(1)
            .then((r: any[]) => r[0]);

        if (!tx) {
            console.warn(`Midtrans webhook: transaction ${order_id} not found`);
            return c.json({ ok: true });
        }

        // Already processed? (type sudah 'topup' dan bukan 'topup_pending')
        if (tx.type === 'topup' && !tx.description?.includes('pending')) {
            return c.json({ ok: true, alreadyProcessed: true });
        }

        const userId = tx.userId;
        const coinAmount = tx.amount;

        if (successStatuses.includes(transaction_status)) {
            // Update user purchasedCoins
            await db.update(users)
                .set({
                    purchasedCoins: sql`${users.purchasedCoins} + ${coinAmount}`,
                    updatedAt: new Date(),
                })
                .where(eq(users.id, userId));

            // Update transaction to success
            await db.update(coinTransactions)
                .set({
                    type: 'topup',
                    balanceAfter: sql`(${users.coins} + ${users.purchasedCoins})`,
                    description: tx.description.replace('Top Up', 'Top Up Success'),
                })
                .where(eq(coinTransactions.reference, order_id.toString()));

            console.log(`Midtrans webhook: added ${coinAmount} coins to user ${userId}`);
        } else if (failedStatuses.includes(transaction_status)) {
            // Mark as failed
            await db.update(coinTransactions)
                .set({
                    description: tx.description + ' (FAILED)',
                })
                .where(eq(coinTransactions.reference, order_id.toString()));

            console.log(`Midtrans webhook: marked ${order_id} as failed`);
        } else if (pendingStatuses.includes(transaction_status)) {
            // Keep as pending
            console.log(`Midtrans webhook: transaction ${order_id} still pending`);
        }

        return c.json({ ok: true });
    } catch (error: any) {
        console.error('Midtrans webhook error:', error);
        return c.json({ error: 'Webhook processing failed' }, 500);
    }
});

export default webhooksRoute;

