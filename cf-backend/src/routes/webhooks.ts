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

            default:
                console.log(`RevenueCat webhook: unhandled event type ${type}`);
        }
    } catch (err) {
        console.error('RevenueCat webhook DB error:', err);
        return c.json({ error: 'DB error' }, 500);
    }

    return c.json({ ok: true });
});

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

        const { order_id, transaction_status, gross_amount, status_code } = body;
        console.log(`Midtrans webhook: order_id=${order_id}, status=${transaction_status}`);

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

        // Already processed?
        if (tx.type === 'topup' && tx.status === 'success') {
            return c.json({ ok: true, alreadyProcessed: true });
        }

        const userId = tx.userId;
        const coinAmount = tx.amount;

        if (successStatuses.includes(transaction_status)) {
            // Update user coins
            await db.update(users)
                .set({
                    coins: sql`${users.coins} + ${coinAmount}`,
                    updatedAt: new Date(),
                })
                .where(eq(users.id, userId));

            // Update transaction to success
            await db.update(coinTransactions)
                .set({
                    type: 'topup',
                    status: 'success',
                    balanceAfter: sql`(${users.coins} + ${coinAmount})`,
                    description: tx.description.replace('Top Up', 'Top Up Success'),
                })
                .where(eq(coinTransactions.reference, order_id.toString()));

            console.log(`Midtrans webhook: added ${coinAmount} coins to user ${userId}`);
        } else if (failedStatuses.includes(transaction_status)) {
            // Mark as failed
            await db.update(coinTransactions)
                .set({
                    status: 'failed',
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

