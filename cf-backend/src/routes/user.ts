import { Hono } from 'hono';
import { eq, and, desc, sql, asc } from 'drizzle-orm';
import { getDb, parseJsonArray } from '../db';
import { watchlist, favorites, collections, watchHistory, dramas, episodes } from '../db/schema';
import { Env, requireAuth } from '../middleware/auth';

const userRoute = new Hono<Env>();
userRoute.use('*', requireAuth);

// ==================== WATCHLIST ====================

userRoute.get('/watchlist', async (c) => {
    try {
        const userId = c.get('user').id;
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const items = await db.select({
            id: watchlist.id,
            addedAt: watchlist.addedAt,
            drama: dramas,
        }).from(watchlist)
            .innerJoin(dramas, eq(watchlist.dramaId, dramas.id))
            .where(eq(watchlist.userId, userId))
            .orderBy(desc(watchlist.addedAt));

        const enriched = items.map(item => ({
            ...item,
            drama: { ...item.drama, genres: parseJsonArray(item.drama.genres), cast: parseJsonArray(item.drama.cast) },
        }));

        return c.json(enriched);
    } catch (error) {
        console.error('Get watchlist error:', error);
        return c.json({ error: 'Failed to get watchlist' }, 500);
    }
});

userRoute.post('/watchlist', async (c) => {
    try {
        const userId = c.get('user').id;
        const { dramaId } = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const existing = await db.select().from(watchlist)
            .where(and(eq(watchlist.userId, userId), eq(watchlist.dramaId, dramaId)))
            .limit(1).then((r: any[]) => r[0]);

        if (existing) return c.json({ success: true, message: 'Already in watchlist' });

        await db.insert(watchlist).values({ userId, dramaId });
        return c.json({ success: true });
    } catch (error) {
        console.error('Add to watchlist error:', error);
        return c.json({ error: 'Failed to add to watchlist' }, 500);
    }
});

userRoute.delete('/watchlist/:dramaId', async (c) => {
    try {
        const userId = c.get('user').id;
        const dramaId = c.req.param('dramaId');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        await db.delete(watchlist)
            .where(and(eq(watchlist.userId, userId), eq(watchlist.dramaId, dramaId)));

        return c.json({ success: true });
    } catch (error) {
        console.error('Remove from watchlist error:', error);
        return c.json({ error: 'Failed to remove from watchlist' }, 500);
    }
});

userRoute.get('/watchlist/:dramaId/check', async (c) => {
    try {
        const userId = c.get('user').id;
        const dramaId = c.req.param('dramaId');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const item = await db.select().from(watchlist)
            .where(and(eq(watchlist.userId, userId), eq(watchlist.dramaId, dramaId)))
            .limit(1).then((r: any[]) => r[0]);

        return c.json({ inWatchlist: !!item });
    } catch (error) {
        console.error('Check watchlist error:', error);
        return c.json({ error: 'Failed to check watchlist' }, 500);
    }
});

// ==================== FAVORITES ====================

userRoute.get('/favorites', async (c) => {
    try {
        const userId = c.get('user').id;
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const items = await db.select({
            id: favorites.id,
            addedAt: favorites.addedAt,
            drama: dramas,
        }).from(favorites)
            .innerJoin(dramas, eq(favorites.dramaId, dramas.id))
            .where(eq(favorites.userId, userId))
            .orderBy(desc(favorites.addedAt));

        const enriched = items.map(item => ({
            ...item,
            drama: { ...item.drama, genres: parseJsonArray(item.drama.genres), cast: parseJsonArray(item.drama.cast) },
        }));

        return c.json(enriched);
    } catch (error) {
        console.error('Get favorites error:', error);
        return c.json({ error: 'Failed to get favorites' }, 500);
    }
});

userRoute.post('/favorites', async (c) => {
    try {
        const userId = c.get('user').id;
        const { dramaId } = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const existing = await db.select().from(favorites)
            .where(and(eq(favorites.userId, userId), eq(favorites.dramaId, dramaId)))
            .limit(1).then((r: any[]) => r[0]);

        if (existing) return c.json({ success: true, message: 'Already in favorites' });

        await db.insert(favorites).values({ userId, dramaId });
        return c.json({ success: true });
    } catch (error) {
        console.error('Add to favorites error:', error);
        return c.json({ error: 'Failed to add to favorites' }, 500);
    }
});

userRoute.delete('/favorites/:dramaId', async (c) => {
    try {
        const userId = c.get('user').id;
        const dramaId = c.req.param('dramaId');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        await db.delete(favorites)
            .where(and(eq(favorites.userId, userId), eq(favorites.dramaId, dramaId)));

        return c.json({ success: true });
    } catch (error) {
        console.error('Remove from favorites error:', error);
        return c.json({ error: 'Failed to remove from favorites' }, 500);
    }
});

userRoute.get('/favorites/:dramaId/check', async (c) => {
    try {
        const userId = c.get('user').id;
        const dramaId = c.req.param('dramaId');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const item = await db.select().from(favorites)
            .where(and(eq(favorites.userId, userId), eq(favorites.dramaId, dramaId)))
            .limit(1).then((r: any[]) => r[0]);

        return c.json({ inFavorites: !!item });
    } catch (error) {
        console.error('Check favorites error:', error);
        return c.json({ error: 'Failed to check favorites' }, 500);
    }
});

// ==================== COLLECTION ====================

userRoute.get('/collection', async (c) => {
    try {
        const userId = c.get('user').id;
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const items = await db.select({
            id: collections.id,
            addedAt: collections.addedAt,
            notifyNewEpisode: collections.notifyNewEpisode,
            drama: dramas,
        }).from(collections)
            .innerJoin(dramas, eq(collections.dramaId, dramas.id))
            .where(eq(collections.userId, userId))
            .orderBy(desc(collections.addedAt));

        const enriched = items.map(item => ({
            ...item,
            drama: { ...item.drama, genres: parseJsonArray(item.drama.genres), cast: parseJsonArray(item.drama.cast) },
        }));

        return c.json(enriched);
    } catch (error) {
        console.error('Get collection error:', error);
        return c.json({ error: 'Failed to get collection' }, 500);
    }
});

userRoute.post('/collection', async (c) => {
    try {
        const userId = c.get('user').id;
        const { dramaId, notifyNewEpisode = true } = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const existing = await db.select().from(collections)
            .where(and(eq(collections.userId, userId), eq(collections.dramaId, dramaId)))
            .limit(1).then((r: any[]) => r[0]);

        if (existing) return c.json({ success: true, message: 'Already in collection' });

        await db.insert(collections).values({ userId, dramaId, notifyNewEpisode });
        return c.json({ success: true });
    } catch (error) {
        console.error('Add to collection error:', error);
        return c.json({ error: 'Failed to add to collection' }, 500);
    }
});

userRoute.delete('/collection/:dramaId', async (c) => {
    try {
        const userId = c.get('user').id;
        const dramaId = c.req.param('dramaId');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        await db.delete(collections)
            .where(and(eq(collections.userId, userId), eq(collections.dramaId, dramaId)));

        return c.json({ success: true });
    } catch (error) {
        console.error('Remove from collection error:', error);
        return c.json({ error: 'Failed to remove from collection' }, 500);
    }
});

userRoute.get('/collection/:dramaId/check', async (c) => {
    try {
        const userId = c.get('user').id;
        const dramaId = c.req.param('dramaId');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const item = await db.select().from(collections)
            .where(and(eq(collections.userId, userId), eq(collections.dramaId, dramaId)))
            .limit(1).then((r: any[]) => r[0]);

        return c.json({ inCollection: !!item });
    } catch (error) {
        console.error('Check collection error:', error);
        return c.json({ error: 'Failed to check collection' }, 500);
    }
});

// ==================== WATCH HISTORY ====================

userRoute.get('/history', async (c) => {
    try {
        const userId = c.get('user').id;
        const page = parseInt(c.req.query('page') || '1');
        const limit = parseInt(c.req.query('limit') || '20');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const items = await db.select({
            id: watchHistory.id,
            dramaId: watchHistory.dramaId,
            episodeNumber: watchHistory.episodeNumber,
            progress: watchHistory.progress,
            watchedAt: watchHistory.watchedAt,
            drama: dramas,
        }).from(watchHistory)
            .innerJoin(dramas, eq(watchHistory.dramaId, dramas.id))
            .where(eq(watchHistory.userId, userId))
            .orderBy(desc(watchHistory.watchedAt))
            .limit(limit)
            .offset((page - 1) * limit);

        const totalResult = await db.select({ count: sql<number>`count(*)` }).from(watchHistory)
            .where(eq(watchHistory.userId, userId));

        const enriched = items.map(item => ({
            ...item,
            drama: { ...item.drama, genres: parseJsonArray(item.drama.genres), cast: parseJsonArray(item.drama.cast) },
        }));

        return c.json({ history: enriched, total: totalResult[0]?.count || 0, page, limit });
    } catch (error) {
        console.error('Get history error:', error);
        return c.json({ error: 'Failed to get history' }, 500);
    }
});

userRoute.post('/history', async (c) => {
    try {
        const userId = c.get('user').id;
        const { dramaId, episodeNumber, progress } = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        // Find episode
        const episode = await db.select().from(episodes)
            .where(and(eq(episodes.dramaId, dramaId), eq(episodes.episodeNumber, episodeNumber)))
            .limit(1).then((r: any[]) => r[0]);

        if (!episode) return c.json({ error: 'Episode not found' }, 404);

        // Upsert history
        const existing = await db.select().from(watchHistory)
            .where(and(eq(watchHistory.userId, userId), eq(watchHistory.dramaId, dramaId)))
            .limit(1).then((r: any[]) => r[0]);

        let history;
        if (existing) {
            [history] = await db.update(watchHistory)
                .set({
                    episodeId: episode.id,
                    episodeNumber,
                    progress: progress || 0,
                    watchedAt: new Date(),
                })
                .where(eq(watchHistory.id, existing.id))
                .returning();
        } else {
            [history] = await db.insert(watchHistory).values({
                userId,
                dramaId,
                episodeId: episode.id,
                episodeNumber,
                progress: progress || 0,
            }).returning();
        }

        return c.json(history);
    } catch (error) {
        console.error('Update history error:', error);
        return c.json({ error: 'Failed to update history' }, 500);
    }
});

userRoute.delete('/history/:dramaId', async (c) => {
    try {
        const userId = c.get('user').id;
        const dramaId = c.req.param('dramaId');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        await db.delete(watchHistory)
            .where(and(eq(watchHistory.userId, userId), eq(watchHistory.dramaId, dramaId)));

        return c.json({ success: true });
    } catch (error) {
        console.error('Delete history error:', error);
        return c.json({ error: 'Failed to delete history' }, 500);
    }
});

userRoute.delete('/history', async (c) => {
    try {
        const userId = c.get('user').id;
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        await db.delete(watchHistory).where(eq(watchHistory.userId, userId));
        return c.json({ success: true });
    } catch (error) {
        console.error('Clear history error:', error);
        return c.json({ error: 'Failed to clear history' }, 500);
    }
});

// GET /api/user/continue-watching
userRoute.get('/continue-watching', async (c) => {
    try {
        const userId = c.get('user').id;
        const limit = parseInt(c.req.query('limit') || '5');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const items = await db.select({
            id: watchHistory.id,
            episodeNumber: watchHistory.episodeNumber,
            progress: watchHistory.progress,
            watchedAt: watchHistory.watchedAt,
            drama: dramas,
        }).from(watchHistory)
            .innerJoin(dramas, eq(watchHistory.dramaId, dramas.id))
            .where(and(eq(watchHistory.userId, userId), sql`${watchHistory.progress} < 100`))
            .orderBy(desc(watchHistory.watchedAt))
            .limit(limit);

        const enriched = items.map(item => ({
            ...item,
            drama: { ...item.drama, genres: parseJsonArray(item.drama.genres), cast: parseJsonArray(item.drama.cast) },
        }));

        return c.json(enriched);
    } catch (error) {
        console.error('Get continue watching error:', error);
        return c.json({ error: 'Failed to get continue watching' }, 500);
    }
});

export default userRoute;
