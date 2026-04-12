import { Hono } from 'hono';
import { eq } from 'drizzle-orm';
import { getDb } from '../db';
import { users } from '../db/schema';
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

export default webhooksRoute;
