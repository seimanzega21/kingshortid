import { Hono } from 'hono';
import { eq, and, desc, like, or, sql, ne, gte, asc } from 'drizzle-orm';
import { getDb } from '../db';
import { users, dramas, episodes, watchHistory, watchlist, favorites, collections, coinTransactions, feedbacks } from '../db/schema';
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

        // Online users (updatedAt heartbeat within last 12 hours = active today)
        const twelveHoursAgo = new Date(Date.now() - 12 * 60 * 60 * 1000);
        const onlineResult = await db.select({ count: sql<number>`count(*)` })
            .from(users)
            .where(gte(users.updatedAt, twelveHoursAgo))
            .limit(1).then((r: any[]) => r[0]);

        // Total views
        const viewsResult = await db.select({ total: sql<number>`COALESCE(SUM(views), 0)` })
            .from(dramas)
            .limit(1).then((r: any[]) => r[0]);

        // Data health — match scraper audit criteria
        const [noDescResult, noCoverResult, noEpisodesResult, genericGenreResult] = await Promise.all([
            // Bad description: empty, too short, or equals title
            db.select({ count: sql<number>`count(*)` }).from(dramas)
                .where(and(
                    eq(dramas.isActive, true),
                    sql`(${dramas.description} = '' OR ${dramas.description} = ${dramas.title} OR length(${dramas.description}) < 10)`
                )).limit(1).then((r: any[]) => r[0]),
            // No cover
            db.select({ count: sql<number>`count(*)` }).from(dramas)
                .where(and(eq(dramas.isActive, true), eq(dramas.cover, ''))).limit(1).then((r: any[]) => r[0]),
            // No episodes
            db.select({ count: sql<number>`count(*)` }).from(dramas)
                .where(and(eq(dramas.isActive, true), eq(dramas.totalEpisodes, 0))).limit(1).then((r: any[]) => r[0]),
            // Generic genre: empty array, or single "Drama" genre
            db.select({ count: sql<number>`count(*)` }).from(dramas)
                .where(and(
                    eq(dramas.isActive, true),
                    sql`(${dramas.genres}::jsonb = '[]'::jsonb OR ${dramas.genres}::jsonb = '["Drama"]'::jsonb OR jsonb_array_length(${dramas.genres}::jsonb) = 0)`
                )).limit(1).then((r: any[]) => r[0]),
        ]);

        const activeDramaCount = activeDramasResult?.count || 0;
        const noDesc = noDescResult?.count || 0;
        const noCover = noCoverResult?.count || 0;
        const noEps = noEpisodesResult?.count || 0;
        const genericGenre = genericGenreResult?.count || 0;

        // Count dramas with ANY issue (avoid double-counting)
        const issueCountResult = await db.select({ count: sql<number>`count(*)` }).from(dramas)
            .where(and(
                eq(dramas.isActive, true),
                sql`(
                    ${dramas.description} = '' OR ${dramas.description} = ${dramas.title} OR length(${dramas.description}) < 10
                    OR ${dramas.cover} = ''
                    OR ${dramas.totalEpisodes} = 0
                    OR ${dramas.genres}::jsonb = '[]'::jsonb OR ${dramas.genres}::jsonb = '["Drama"]'::jsonb OR jsonb_array_length(${dramas.genres}::jsonb) = 0
                )`
            )).limit(1).then((r: any[]) => r[0]);
        const totalWithIssues = issueCountResult?.count || 0;

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
                healthy: Math.max(0, activeDramaCount - totalWithIssues),
                genericGenre,
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

// ==================== ANALYTICS ====================
adminRoute.get('/analytics', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const period = c.req.query('period') || '7d';

        // Calculate startDate based on period
        const now = new Date();
        const startDate = new Date();
        if (period === '7d') startDate.setDate(now.getDate() - 7);
        else if (period === '30d') startDate.setDate(now.getDate() - 30);
        else startDate.setDate(now.getDate() - 90);

        // Group views by date
        const dailyViewsQuery = await db.execute(sql`
            SELECT DATE(watched_at) as date, COUNT(*) as count 
            FROM watch_history 
            WHERE watched_at >= ${startDate.toISOString()}
            GROUP BY DATE(watched_at)
            ORDER BY DATE(watched_at) ASC
        `);

        // Group user growth by date
        const userGrowthQuery = await db.execute(sql`
            SELECT DATE(created_at) as date, COUNT(*) as count 
            FROM users 
            WHERE created_at >= ${startDate.toISOString()}
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at) ASC
        `);

        // Top Dramas
        const topDramas = await db.select({
            id: dramas.id,
            title: dramas.title,
            views: dramas.views,
            rating: dramas.rating,
            episodes: dramas.totalEpisodes,
        }).from(dramas).orderBy(desc(dramas.views)).limit(10);

        // Total stats
        const [totalViewsRes, totalUsersRes, totalDramasRes, totalRevenueRes] = await Promise.all([
            db.select({ total: sql<number>`COALESCE(SUM(views), 0)` }).from(dramas).limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` }).from(users).limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` }).from(dramas).limit(1).then((r: any[]) => r[0]),
            db.select({ total: sql<number>`COALESCE(SUM(amount), 0)` }).from(coinTransactions).where(eq(coinTransactions.type, 'topup')).limit(1).then((r: any[]) => r[0]),
        ]);

        // Helper to format days 
        const dayNames = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab'];
        const formatDailyData = (queryResult: any) => {
            const result = [];
            for (let d = new Date(startDate); d <= now; d.setDate(d.getDate() + 1)) {
                const dateStr = d.toISOString().split('T')[0];
                const found = (queryResult as any).rows?.find((r: any) => {
                    const rowDateStr = new Date(r.date + 'T00:00:00Z').toISOString().split('T')[0];
                    return rowDateStr === dateStr;
                });
                result.push({
                    name: dayNames[d.getDay()],
                    date: dateStr,
                    value: found ? Number(found.count) : 0
                });
            }
            return period === '7d' ? result.slice(-7) : result;
        };

        const viewershipData = formatDailyData(dailyViewsQuery);
        const userGrowthData = formatDailyData(userGrowthQuery);

        return c.json({
            viewershipData,
            userGrowthData,
            topDramas,
            stats: {
                totalViews: Number(totalViewsRes?.total) || 0,
                totalUsers: Number(totalUsersRes?.count) || 0,
                totalDramas: Number(totalDramasRes?.count) || 0,
                totalRevenue: Number(totalRevenueRes?.total) || 0,
            }
        });

    } catch (error) {
        console.error('Admin analytics error:', error);
        return c.json({ error: 'Failed to fetch analytics data' }, 500);
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
            const count = (result as any).meta?.changes || 0;
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

// ==================== UPDATE DRAMA ====================
adminRoute.patch('/dramas/:id', async (c) => {
    try {
        const id = c.req.param('id');
        const body = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const updateData: Record<string, any> = { updatedAt: new Date() };
        if (body.genres !== undefined) updateData.genres = body.genres;
        if (body.title !== undefined) updateData.title = body.title;
        if (body.description !== undefined) updateData.description = body.description;
        if (typeof body.isActive === 'boolean') updateData.isActive = body.isActive;
        if (typeof body.isVip === 'boolean') updateData.isVip = body.isVip;

        const [updated] = await db.update(dramas)
            .set(updateData)
            .where(eq(dramas.id, id))
            .returning({ id: dramas.id, title: dramas.title, genres: dramas.genres });

        if (!updated) return c.json({ error: 'Drama not found' }, 404);
        return c.json(updated);
    } catch (error) {
        console.error('Admin update drama error:', error);
        return c.json({ error: 'Failed to update drama' }, 500);
    }
});

// ==================== RUN MIGRATION (one-time) ====================
adminRoute.post('/run-migration', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        // Add video_url_540p column if not exists
        await db.execute(sql`ALTER TABLE episodes ADD COLUMN IF NOT EXISTS video_url_540p text`);

        // Verify column exists
        const check = await db.execute(sql`
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'episodes' AND column_name = 'video_url_540p'
        `);

        const columnExists = (check as any).rows && (check as any).rows.length > 0;
        return c.json({
            ok: columnExists,
            message: columnExists
                ? 'Migration complete: video_url_540p column now exists in episodes table'
                : 'ALTER ran but column not found - check DB manually',
        });
    } catch (error: any) {
        console.error('Migration error:', error);
        return c.json({ ok: false, error: error?.message || String(error) }, 500);
    }
});

// ==================== FEEDBACKS ====================

adminRoute.get('/feedbacks', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        
        const allFeedbacks = await db
            .select({
                id: feedbacks.id,
                message: feedbacks.message,
                status: feedbacks.status,
                createdAt: feedbacks.createdAt,
                user: {
                    id: users.id,
                    name: users.name,
                    email: users.email,
                }
            })
            .from(feedbacks)
            .leftJoin(users, eq(feedbacks.userId, users.id))
            .orderBy(desc(feedbacks.createdAt));

        return c.json({ feedbacks: allFeedbacks });
    } catch (error) {
        console.error('Get feedbacks error:', error);
        return c.json({ error: 'Failed to fetch feedbacks' }, 500);
    }
});

adminRoute.put('/feedbacks/:id', async (c) => {
    try {
        const { id } = c.req.param();
        const { status } = await c.req.json();
        
        if (!['unread', 'read', 'resolved'].includes(status)) {
            return c.json({ error: 'Invalid status' }, 400);
        }

        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        
        await db.update(feedbacks)
            .set({ status })
            .where(eq(feedbacks.id, id));

        return c.json({ success: true });
    } catch (error) {
        console.error('Update feedback error:', error);
        return c.json({ error: 'Failed to update feedback status' }, 500);
    }
});

adminRoute.delete('/feedbacks/:id', async (c) => {
    try {
        const { id } = c.req.param();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        
        await db.delete(feedbacks).where(eq(feedbacks.id, id));

        return c.json({ success: true });
    } catch (error) {
        console.error('Delete feedback error:', error);
        return c.json({ error: 'Failed to delete feedback' }, 500);
    }
});

export default adminRoute;


