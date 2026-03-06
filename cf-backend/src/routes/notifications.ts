import { Hono } from 'hono';
import { eq, and, desc, sql, gte } from 'drizzle-orm';
import { getDb } from '../db';
import { notifications, users } from '../db/schema';
import { Env, requireAuth } from '../middleware/auth';

const notificationsRoute = new Hono<Env>();
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
