import { Hono } from 'hono';
import { eq, and, desc, sql, gte } from 'drizzle-orm';
import { getDb } from '../db';
import { notifications, users } from '../db/schema';
import { Env, requireAuth } from '../middleware/auth';
import { sendBroadcastNotification } from '../services/fcm';

const notificationsRoute = new Hono<Env>();

// POST /api/notifications/broadcast — Admin-only broadcast push notification
notificationsRoute.post('/broadcast', async (c) => {
    try {
        const apiKey = c.req.header('X-Admin-Key') || c.req.header('Authorization')?.replace('Bearer ', '');
        if (apiKey !== c.env.ADMIN_API_KEY) {
            return c.json({ error: 'Unauthorized' }, 401);
        }

        const { title, body, type = 'system' } = await c.req.json();
        if (!title || !body) {
            return c.json({ error: 'Title and body are required' }, 400);
        }

        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        // 1. Insert in-app notification for all active users
        const allUsers = await db.select({ id: users.id }).from(users).where(eq(users.isActive, true));

        if (allUsers.length > 0) {
            const notifValues = allUsers.map(u => ({
                userId: u.id,
                title,
                body,
                type,
                read: false,
            }));

            // Insert in batches of 50
            for (let i = 0; i < notifValues.length; i += 50) {
                await db.insert(notifications).values(notifValues.slice(i, i + 50));
            }
        }

        // 2. Send FCM push notification to all users with push tokens
        let fcmResult = { sent: 0, failed: 0, total: 0 };
        try {
            fcmResult = await sendBroadcastNotification(
                c.env.SUPABASE_URL,
                c.env.SUPABASE_DB_PASSWORD,
                title,
                body,
                { type },
            );
        } catch (e) {
            console.error('FCM broadcast error:', e);
        }

        return c.json({
            success: true,
            message: `Notification sent to ${allUsers.length} users`,
            inApp: allUsers.length,
            push: fcmResult,
        });
    } catch (error) {
        console.error('Broadcast notification error:', error);
        return c.json({ error: 'Failed to send broadcast' }, 500);
    }
});

// Auth required for user-specific endpoints
notificationsRoute.use('*', requireAuth);

// GET /api/notifications
notificationsRoute.get('/', async (c) => {
    try {
        const userId = c.get('user').id;
        const page = parseInt(c.req.query('page') || '1');
        const limit = parseInt(c.req.query('limit') || '20');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const [items, totalResult, unreadResult] = await Promise.all([
            db.select().from(notifications)
                .where(eq(notifications.userId, userId))
                .orderBy(desc(notifications.createdAt))
                .limit(limit)
                .offset((page - 1) * limit),
            db.select({ count: sql<number>`count(*)` }).from(notifications)
                .where(eq(notifications.userId, userId)),
            db.select({ count: sql<number>`count(*)` }).from(notifications)
                .where(and(eq(notifications.userId, userId), eq(notifications.read, false))),
        ]);

        return c.json({
            notifications: items,
            total: totalResult[0]?.count || 0,
            unread: unreadResult[0]?.count || 0,
            page,
            limit,
        });
    } catch (error) {
        console.error('Get notifications error:', error);
        return c.json({ error: 'Failed to get notifications' }, 500);
    }
});

// PUT /api/notifications/:id/read
notificationsRoute.put('/:id/read', async (c) => {
    try {
        const userId = c.get('user').id;
        const id = c.req.param('id');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        await db.update(notifications)
            .set({ read: true })
            .where(and(eq(notifications.id, id), eq(notifications.userId, userId)));

        return c.json({ success: true });
    } catch (error) {
        console.error('Read notification error:', error);
        return c.json({ error: 'Failed to read notification' }, 500);
    }
});

// PUT /api/notifications/read-all
notificationsRoute.put('/read-all', async (c) => {
    try {
        const userId = c.get('user').id;
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        await db.update(notifications)
            .set({ read: true })
            .where(and(eq(notifications.userId, userId), eq(notifications.read, false)));

        return c.json({ success: true });
    } catch (error) {
        console.error('Read all notifications error:', error);
        return c.json({ error: 'Failed to read all notifications' }, 500);
    }
});

// DELETE /api/notifications/:id
notificationsRoute.delete('/:id', async (c) => {
    try {
        const userId = c.get('user').id;
        const id = c.req.param('id');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        await db.delete(notifications)
            .where(and(eq(notifications.id, id), eq(notifications.userId, userId)));

        return c.json({ success: true });
    } catch (error) {
        console.error('Delete notification error:', error);
        return c.json({ error: 'Failed to delete notification' }, 500);
    }
});

// DELETE /api/notifications - Clear all
notificationsRoute.delete('/', async (c) => {
    try {
        const userId = c.get('user').id;
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        await db.delete(notifications).where(eq(notifications.userId, userId));
        return c.json({ success: true });
    } catch (error) {
        console.error('Clear notifications error:', error);
        return c.json({ error: 'Failed to clear notifications' }, 500);
    }
});

// PUT /api/notifications/settings
notificationsRoute.put('/settings', async (c) => {
    try {
        const userId = c.get('user').id;
        const { pushToken, notifyEpisodes, notifyCoins, notifySystem } = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const updateData: Record<string, any> = {};
        if (pushToken !== undefined) updateData.pushToken = pushToken;
        if (notifyEpisodes !== undefined) updateData.notifyEpisodes = notifyEpisodes;
        if (notifyCoins !== undefined) updateData.notifyCoins = notifyCoins;
        if (notifySystem !== undefined) updateData.notifySystem = notifySystem;
        updateData.updatedAt = new Date();

        await db.update(users).set(updateData).where(eq(users.id, userId));

        return c.json({ success: true, message: 'Pengaturan notifikasi berhasil diperbarui' });
    } catch (error) {
        console.error('Update notification settings error:', error);
        return c.json({ error: 'Failed to update notification settings' }, 500);
    }
});

export default notificationsRoute;
