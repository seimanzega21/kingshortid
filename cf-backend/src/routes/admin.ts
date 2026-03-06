import { Hono } from 'hono';
import { eq, and, desc, like, or, sql, ne, gte, asc } from 'drizzle-orm';
import { getDb } from '../db';
import { users, dramas, episodes, watchHistory, watchlist, favorites, collections, coinTransactions } from '../db/schema';
import { requireAdmin, getAuthUser } from '../middleware/auth';
import type { Env } from '../middleware/auth';

const adminRoute = new Hono<Env>();

// Admin auth: API key (for admin panel proxy) OR JWT admin user
adminRoute.use('*', async (c, next) => {
    // Check API key first (service-to-service)
    const apiKey = c.req.header('X-Admin-Key');
    if (apiKey && apiKey === (c.env as any).ADMIN_API_KEY) {
        return next();
    }
    // Fallback to JWT admin auth
    return requireAdmin(c, next);
});

// ==================== DASHBOARD ====================
adminRoute.get('/dashboard', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const twentyFourHoursAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);

        // Basic stats
        const [
            totalUsersResult,
            activeUsersResult,
            totalDramasResult,
            activeDramasResult,
            inactiveDramasResult,
            totalEpisodesResult,
        ] = await Promise.all([
            db.select({ count: sql<number>`count(*)` }).from(users).limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` }).from(users).where(eq(users.role, 'user')).limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` }).from(dramas).limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` }).from(dramas).where(eq(dramas.isActive, true)).limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` }).from(dramas).where(eq(dramas.isActive, false)).limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` }).from(episodes).limit(1).then((r: any[]) => r[0]),
        ]);

        // Online users (active in last 24h)
        const onlineResult = await db.select({ count: sql<number>`count(DISTINCT user_id)` })
            .from(watchHistory)
            .where(gte(watchHistory.watchedAt, twentyFourHoursAgo))
            .limit(1).then((r: any[]) => r[0]);

        // Total views
        const viewsResult = await db.select({ total: sql<number>`COALESCE(SUM(views), 0)` })
            .from(dramas)
            .limit(1).then((r: any[]) => r[0]);

        // Data health
        const [noDescResult, noCoverResult, noEpisodesResult] = await Promise.all([
            db.select({ count: sql<number>`count(*)` }).from(dramas)
                .where(and(eq(dramas.isActive, true), eq(dramas.description, ''))).limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` }).from(dramas)
                .where(and(eq(dramas.isActive, true), eq(dramas.cover, ''))).limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` }).from(dramas)
                .where(and(eq(dramas.isActive, true), eq(dramas.totalEpisodes, 0))).limit(1).then((r: any[]) => r[0]),
        ]);

        const activeDramaCount = activeDramasResult?.count || 0;
        const noDesc = noDescResult?.count || 0;
        const noCover = noCoverResult?.count || 0;
        const noEps = noEpisodesResult?.count || 0;

        // Recent users
        const recentUsers = await db.select({
            id: users.id,
            name: users.name,
            email: users.email,
            avatar: users.avatar,
            createdAt: users.createdAt,
            role: users.role,
            isActive: users.isActive,
        }).from(users).orderBy(desc(users.createdAt)).limit(5);

        // Popular dramas
        const popularDramas = await db.select({
            id: dramas.id,
            title: dramas.title,
            cover: dramas.cover,
            views: dramas.views,
            rating: dramas.rating,
            status: dramas.status,
        }).from(dramas)
            .where(eq(dramas.isActive, true))
            .orderBy(desc(dramas.views))
            .limit(8);

        // Recent dramas
        const recentDramas = await db.select({
            id: dramas.id,
            title: dramas.title,
            cover: dramas.cover,
            totalEpisodes: dramas.totalEpisodes,
            createdAt: dramas.createdAt,
            status: dramas.status,
            genres: dramas.genres,
        }).from(dramas).orderBy(desc(dramas.createdAt)).limit(5);

        return c.json({
            stats: {
                totalUsers: totalUsersResult?.count || 0,
                activeUsers: activeUsersResult?.count || 0,
                onlineUsers: onlineResult?.count || 0,
                totalDramas: totalDramasResult?.count || 0,
                activeDramas: activeDramaCount,
                inactiveDramas: inactiveDramasResult?.count || 0,
                totalEpisodes: totalEpisodesResult?.count || 0,
                totalViews: viewsResult?.total || 0,
            },
            dataHealth: {
                healthy: Math.max(0, activeDramaCount - noDesc - noCover - noEps),
                genericGenre: 0, // D1 doesn't store genres as array natively
                noDescription: noDesc,
                noCover: noCover,
                noEpisodes: noEps,
                deactivated: inactiveDramasResult?.count || 0,
            },
            recentUsers,
            popularDramas,
            recentDramas,
        });
    } catch (error) {
        console.error('Admin dashboard error:', error);
        return c.json({ error: 'Failed to fetch dashboard stats' }, 500);
    }
});

// ==================== LIST USERS ====================
adminRoute.get('/users', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const page = parseInt(c.req.query('page') || '1');
        const limit = parseInt(c.req.query('limit') || '10');
        const search = c.req.query('q');
        const role = c.req.query('role');
        const accountType = c.req.query('accountType');

        let conditions = [];
        if (role) conditions.push(eq(users.role, role));
        if (accountType === 'guest') conditions.push(eq(users.isGuest, true));
        else if (accountType === 'google') conditions.push(eq(users.provider, 'google'));
        else if (accountType === 'registered') conditions.push(eq(users.isGuest, false));
        if (search) {
            conditions.push(or(
                like(users.name, `%${search}%`),
                like(users.email, `%${search}%`),
            )!);
        }

        const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

        const [userList, totalResult] = await Promise.all([
            db.select({
                id: users.id,
                name: users.name,
                email: users.email,
                role: users.role,
                coins: users.coins,
                isActive: users.isActive,
                isGuest: users.isGuest,
                provider: users.provider,
                createdAt: users.createdAt,
            }).from(users)
                .where(whereClause)
                .orderBy(desc(users.createdAt))
                .limit(limit)
                .offset((page - 1) * limit),
            db.select({ count: sql<number>`count(*)` })
                .from(users)
                .where(whereClause)
                .limit(1).then((r: any[]) => r[0]),
        ]);

        return c.json({
            users: userList,
            total: totalResult?.count || 0,
            page,
            pages: Math.ceil((totalResult?.count || 0) / limit),
        });
    } catch (error) {
        console.error('Admin list users error:', error);
        return c.json({ error: 'Failed to fetch users' }, 500);
    }
});

// ==================== USER DETAIL ====================
adminRoute.get('/users/:id', async (c) => {
    try {
        const id = c.req.param('id');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const user = await db.select().from(users).where(eq(users.id, id)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);

        // Counts
        const [watchHistoryCount, watchlistCount, favoritesCount, coinTxCount] = await Promise.all([
            db.select({ count: sql<number>`count(*)` }).from(watchHistory).where(eq(watchHistory.userId, id)).limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` }).from(watchlist).where(eq(watchlist.userId, id)).limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` }).from(favorites).where(eq(favorites.userId, id)).limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` }).from(coinTransactions).where(eq(coinTransactions.userId, id)).limit(1).then((r: any[]) => r[0]),
        ]);

        // Recent watch history with drama info
        const recentHistory = await db.select({
            dramaId: watchHistory.dramaId,
            episodeNumber: watchHistory.episodeNumber,
            progress: watchHistory.progress,
            watchedAt: watchHistory.watchedAt,
            dramaTitle: dramas.title,
            dramaCover: dramas.cover,
        }).from(watchHistory)
            .leftJoin(dramas, eq(watchHistory.dramaId, dramas.id))
            .where(eq(watchHistory.userId, id))
            .orderBy(desc(watchHistory.watchedAt))
            .limit(10);

        // Remove password from response
        const { password, ...safeUser } = user;

        return c.json({
            ...safeUser,
            _count: {
                watchHistory: watchHistoryCount?.count || 0,
                watchlist: watchlistCount?.count || 0,
                favorites: favoritesCount?.count || 0,
                coinTransactions: coinTxCount?.count || 0,
                comments: 0,
            },
            recentHistory: recentHistory.map(h => ({
                dramaId: h.dramaId,
                episodeNumber: h.episodeNumber,
                progress: h.progress,
                watchedAt: h.watchedAt,
                drama: { title: h.dramaTitle || '', cover: h.dramaCover || '' },
            })),
        });
    } catch (error) {
        console.error('Admin user detail error:', error);
        return c.json({ error: 'Failed to fetch user' }, 500);
    }
});

// ==================== UPDATE USER ====================
adminRoute.patch('/users/:id', async (c) => {
    try {
        const id = c.req.param('id');
        const body = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const updateData: Record<string, any> = { updatedAt: new Date() };

        if (typeof body.isActive === 'boolean') updateData.isActive = body.isActive;
        if (body.role) updateData.role = body.role;

        // Add coins (increment)
        if (typeof body.coins === 'number' && body.coins > 0) {
            const current = await db.select({ coins: users.coins }).from(users).where(eq(users.id, id)).limit(1).then((r: any[]) => r[0]);
            if (current) updateData.coins = current.coins + body.coins;
        }

        const [updated] = await db.update(users)
            .set(updateData)
            .where(eq(users.id, id))
            .returning();

        return c.json(updated);
    } catch (error) {
        console.error('Admin update user error:', error);
        return c.json({ error: 'Failed to update user' }, 500);
    }
});

// ==================== DELETE USER ====================
adminRoute.delete('/users/:id', async (c) => {
    try {
        const id = c.req.param('id');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const user = await db.select().from(users).where(eq(users.id, id)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ error: 'User not found' }, 404);
        if (user.role === 'admin') return c.json({ error: 'Cannot delete admin users' }, 403);

        await db.delete(users).where(eq(users.id, id));
        return c.json({ message: 'User deleted permanently' });
    } catch (error) {
        console.error('Admin delete user error:', error);
        return c.json({ error: 'Failed to delete user' }, 500);
    }
});

// ==================== BULK DELETE USERS ====================
adminRoute.post('/users/bulk-delete', async (c) => {
    try {
        const { userIds, deleteAll } = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        if (deleteAll) {
            const result = await db.delete(users).where(ne(users.role, 'admin'));
            const count = result.meta?.changes || 0;
            return c.json({ message: `${count} users deleted permanently`, count });
        }

        if (!userIds || userIds.length === 0) {
            return c.json({ error: 'userIds array is required' }, 400);
        }

        let deleted = 0;
        for (const uid of userIds) {
            const user = await db.select({ role: users.role }).from(users).where(eq(users.id, uid)).limit(1).then((r: any[]) => r[0]);
            if (user && user.role !== 'admin') {
                await db.delete(users).where(eq(users.id, uid));
                deleted++;
            }
        }

        return c.json({ message: `${deleted} users deleted permanently`, count: deleted });
    } catch (error) {
        console.error('Admin bulk delete error:', error);
        return c.json({ error: 'Failed to delete users' }, 500);
    }
});

export default adminRoute;
