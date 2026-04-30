import { Hono } from 'hono';
import { eq, and, desc, like, or, sql, ne, gte, asc, lte, inArray } from 'drizzle-orm';
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

        // 1. Basic Stats
        let statsRow: any = {};
        try {
            const statsQuery = await db.execute(sql`
                SELECT 
                    (SELECT COUNT(*) FROM users) as total_users,
                    (SELECT COUNT(*) FROM users WHERE role = 'user') as active_users,
                    (SELECT COUNT(*) FROM dramas) as total_dramas,
                    (SELECT COUNT(*) FROM dramas WHERE is_active = true) as active_dramas,
                    (SELECT COUNT(*) FROM dramas WHERE is_active = false) as inactive_dramas,
                    (SELECT COUNT(*) FROM episodes) as total_episodes
            `);
            statsRow = Array.isArray(statsQuery) ? statsQuery[0] : (statsQuery as any).rows?.[0] || {};
        } catch (e) {
            console.error("Dashboard Basic Stats Error:", e);
        }

        // 2. Online users
        let onlineCount = 0;
        try {
            const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000);
            const onlineResult = await db.select({ count: sql<number>`count(*)` })
                .from(users)
                .where(gte(users.lastSeen, fiveMinAgo))
                .limit(1).then((r: any[]) => r[0]);
            onlineCount = Number(onlineResult?.count) || 0;
        } catch (e) {
            console.error("Dashboard Online Users Error:", e);
        }

        // 3. VIP users
        let activeVip = 0;
        try {
            const activeVipResult = await db.select({ count: sql<number>`count(*)` })
                .from(users)
                .where(and(
                    eq(users.vipStatus, true),
                    or(
                        sql`${users.vipExpiry} IS NULL`,
                        gte(users.vipExpiry, new Date())
                    )
                ))
                .limit(1).then((r: any[]) => r[0]);
            activeVip = Number(activeVipResult?.count) || 0;
        } catch (e) {
            console.error("Dashboard VIP Stats Error:", e);
        }

        // 4. Views
        let totalViews = 0;
        try {
            const viewsResult = await db.select({ total: sql<number>`COALESCE(SUM(views), 0)` })
                .from(dramas)
                .limit(1).then((r: any[]) => r[0]);
            totalViews = Number(viewsResult?.total) || 0;
        } catch (e) {
            console.error("Dashboard Views Error:", e);
        }

        // 5. Health Data
        let healthRow: any = {};
        try {
            const healthQuery = await db.execute(sql`
                SELECT 
                    COUNT(*) FILTER (WHERE description = '' OR description = title OR length(description) < 10) as no_desc,
                    COUNT(*) FILTER (WHERE cover = '') as no_cover,
                    COUNT(*) FILTER (WHERE total_episodes = 0) as no_eps,
                    COUNT(*) FILTER (WHERE CAST(genres AS TEXT) = '[]' OR CAST(genres AS TEXT) = '["Drama"]' OR jsonb_array_length(genres::jsonb) = 0) as generic_genre,
                    COUNT(*) FILTER (WHERE 
                        (description = '' OR description = title OR length(description) < 10) OR
                        (cover = '') OR
                        (total_episodes = 0) OR
                        (CAST(genres AS TEXT) = '[]' OR jsonb_array_length(genres::jsonb) = 0)
                    ) as total_with_issues
                FROM dramas
                WHERE is_active = true
            `);
            healthRow = Array.isArray(healthQuery) ? healthQuery[0] : (healthQuery as any).rows?.[0] || {};
        } catch (e) {
            console.error("Dashboard Health Query Error:", e);
        }

        const activeDramaCount = Number(statsRow.active_dramas) || 0;
        const noDesc = Number(healthRow.no_desc) || 0;
        const noCover = Number(healthRow.no_cover) || 0;
        const noEps = Number(healthRow.no_eps) || 0;
        const genericGenre = Number(healthRow.generic_genre) || 0;
        const totalWithIssues = Number(healthRow.total_with_issues) || 0;

        // 6. Recent users
        let recentUsers: any[] = [];
        try {
            recentUsers = await db.select({
                id: users.id,
                name: users.name,
                email: users.email,
                avatar: users.avatar,
                createdAt: users.createdAt,
                role: users.role,
                isActive: users.isActive,
            }).from(users).orderBy(desc(users.createdAt)).limit(5);
        } catch (e) {
            console.error("Dashboard Recent Users Error:", e);
        }

        // 7. Popular dramas
        let popularDramas: any[] = [];
        try {
            popularDramas = await db.select({
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
        } catch (e) {
            console.error("Dashboard Popular Dramas Error:", e);
        }

        // 8. Recent dramas
        let recentDramas: any[] = [];
        try {
            recentDramas = await db.select({
                id: dramas.id,
                title: dramas.title,
                cover: dramas.cover,
                totalEpisodes: dramas.totalEpisodes,
                createdAt: dramas.createdAt,
                status: dramas.status,
                genres: dramas.genres,
            }).from(dramas).orderBy(desc(dramas.createdAt)).limit(5);
        } catch (e) {
            console.error("Dashboard Recent Dramas Error:", e);
        }

        return c.json({
            stats: {
                totalUsers: Number(statsRow.total_users) || 0,
                activeUsers: Number(statsRow.active_users) || 0,
                onlineUsers: onlineCount,
                activeVip: activeVip,
                totalDramas: Number(statsRow.total_dramas) || 0,
                activeDramas: activeDramaCount,
                inactiveDramas: Number(statsRow.inactive_dramas) || 0,
                totalEpisodes: Number(statsRow.total_episodes) || 0,
                totalViews: totalViews,
            },
            dataHealth: {
                healthy: Math.max(0, activeDramaCount - totalWithIssues),
                genericGenre,
                noDescription: noDesc,
                noCover: noCover,
                noEpisodes: noEps,
                deactivated: Number(statsRow.inactive_dramas) || 0,
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
            const rows = Array.isArray(queryResult) ? queryResult : (queryResult as any).rows || [];
            const result = [];
            for (let d = new Date(startDate); d <= now; d.setDate(d.getDate() + 1)) {
                const dateStr = d.toISOString().split('T')[0];
                const found = rows.find((r: any) => {
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

// ==================== SYSTEM ACTIONS ====================
// These endpoints are strictly for internal system maintenance scripts

// GET /api/admin/system/m3u8-episodes
adminRoute.get('/system/m3u8-episodes', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        
        // Find all episodes having .m3u8 in their videoUrl
        const m3u8Episodes = await db.select({
            id: episodes.id,
            dramaId: episodes.dramaId,
            episodeNumber: episodes.episodeNumber,
            videoUrl: episodes.videoUrl,
        })
        .from(episodes)
        .where(like(episodes.videoUrl, '%m3u8%'))
        .orderBy(asc(episodes.dramaId), asc(episodes.episodeNumber));
        
        return c.json({ episodes: m3u8Episodes });
    } catch (error) {
        console.error('Fetch m3u8 episodes error:', error);
        return c.json({ error: 'Failed to fetch m3u8 episodes' }, 500);
    }
});

// PUT /api/admin/system/episodes/:id
adminRoute.put('/system/episodes/:id', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const { id } = c.req.param();
        const { videoUrl } = await c.req.json();
        
        if (!videoUrl) return c.json({ error: 'videoUrl is required' }, 400);

        await db.update(episodes)
            .set({ videoUrl })
            .where(eq(episodes.id, id));
            
        return c.json({ success: true, message: 'Episode updated' });
    } catch (error) {
        console.error('Update episode error:', error);
        return c.json({ error: 'Failed to update episode' }, 500);
    }
});

// POST /api/admin/system/delete-small-dramas
adminRoute.post('/system/delete-small-dramas', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const body = await c.req.json().catch(() => ({}));
        const maxEps = typeof body.maxEpisodes === 'number' ? body.maxEpisodes : 2;
        
        // Find all dramas with <= maxEps episodes
        const targetDramas = await db.select({ id: dramas.id, title: dramas.title, cover: dramas.cover, totalEpisodes: dramas.totalEpisodes })
            .from(dramas)
            .where(lte(dramas.totalEpisodes, maxEps));

        if (targetDramas.length === 0) {
            return c.json({ success: true, message: `No dramas found with ${maxEps} or fewer episodes`, count: 0 });
        }

        const dramaIds = targetDramas.map(d => d.id);

        // Delete them (Cascade will handle episodes)
        await db.delete(dramas).where(lte(dramas.totalEpisodes, maxEps));

        return c.json({ success: true, message: `Deleted ${targetDramas.length} dramas`, count: targetDramas.length, deleted: targetDramas });
    } catch (error) {
        console.error('Delete small dramas error:', error);
        return c.json({ error: 'Failed to delete small dramas' }, 500);
    }
});

// ==================== ONLINE USERS ====================
adminRoute.get('/users/online', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000);

        const onlineUsers = await db.select({
            id: users.id,
            name: users.name,
            email: users.email,
            provider: users.provider,
            isGuest: users.isGuest,
            vipStatus: users.vipStatus,
            lastSeen: users.lastSeen,
        }).from(users)
            .where(and(
                gte(users.lastSeen, fiveMinAgo),
                eq(users.isActive, true)
            ))
            .orderBy(desc(users.lastSeen))
            .limit(100);

        const total = await db.select({ count: sql<number>`count(*)` })
            .from(users)
            .where(and(
                gte(users.lastSeen, fiveMinAgo),
                eq(users.isActive, true)
            ))
            .limit(1).then((r: any[]) => r[0]);

        return c.json({ users: onlineUsers, total: total?.count || 0 });
    } catch (error) {
        console.error('Admin online users error:', error);
        return c.json({ error: 'Failed to fetch online users' }, 500);
    }
});

// ==================== VIP STATS ====================
adminRoute.get('/ping-v2', (c) => c.json({ pong: 'v2' }));

adminRoute.get('/stats/vip', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const now = new Date();

        const [activeVip, totalVip, premiumCount] = await Promise.all([
            db.select({ count: sql<number>`count(*)` })
                .from(users)
                .where(and(eq(users.vipStatus, true), or(sql`${users.vipExpiry} IS NULL`, gte(users.vipExpiry, now))))
                .limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` })
                .from(users)
                .where(eq(users.vipStatus, true))
                .limit(1).then((r: any[]) => r[0]),
            db.select({ count: sql<number>`count(*)` })
                .from(users)
                .where(gte(users.coins, 2000))
                .limit(1).then((r: any[]) => r[0]),
        ]);

        return c.json({
            activeVip: activeVip?.count || 0,
            totalVip: totalVip?.count || 0,
            premiumEligible: premiumCount?.count || 0,
        });
    } catch (error) {
        console.error('Admin VIP stats error:', error);
        return c.json({ error: 'Failed to fetch VIP stats' }, 500);
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
        const vipFilter = c.req.query('vip');

        let conditions = [];
        if (role) conditions.push(eq(users.role, role));
        if (accountType === 'guest') conditions.push(eq(users.isGuest, true));
        else if (accountType === 'google') conditions.push(eq(users.provider, 'google'));
        else if (accountType === 'registered') conditions.push(eq(users.isGuest, false));
        if (vipFilter === 'active') {
            conditions.push(eq(users.vipStatus, true));
            conditions.push(or(sql`${users.vipExpiry} IS NULL`, gte(users.vipExpiry, new Date()))!);
        } else if (vipFilter === 'expired') {
            conditions.push(eq(users.vipStatus, true));
            conditions.push(sql`${users.vipExpiry} IS NOT NULL`);
            conditions.push(lte(users.vipExpiry, new Date()));
        } else if (vipFilter === 'regular') {
            conditions.push(eq(users.vipStatus, false));
        }
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
                vipStatus: users.vipStatus,
                vipExpiry: users.vipExpiry,
                lastSeen: users.lastSeen,
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

        // VIP/Premium management
        if (typeof body.vipStatus === 'boolean') updateData.vipStatus = body.vipStatus;
        if (body.vipExpiry !== undefined) updateData.vipExpiry = body.vipExpiry ? new Date(body.vipExpiry) : null;

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


// ==================== CREATE DRAMA (scraper use) ====================
adminRoute.post('/dramas', async (c) => {
    try {
        const body = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        if (!body.title) return c.json({ error: 'title is required' }, 400);
        if (!body.cover) return c.json({ error: 'cover is required' }, 400);

        const existing = await db.select({ id: dramas.id, title: dramas.title })
            .from(dramas).where(eq(dramas.title, body.title)).limit(1).then((r: any[]) => r[0]);

        if (existing) {
            return c.json({ id: existing.id, title: existing.title, already_exists: true });
        }

        const genres = Array.isArray(body.genres) ? body.genres : (body.genres ? [body.genres] : ['Drama']);

        const [created] = await db.insert(dramas).values({
            title: body.title,
            description: body.description || body.title,
            cover: body.cover,
            genres: JSON.stringify(genres),
            tagList: JSON.stringify([]),
            totalEpisodes: body.totalEpisodes || 0,
            status: body.status || (body.isComplete ? 'completed' : 'ongoing'),
            isActive: false,
            isVip: false,
            isFeatured: false,
            country: body.country || 'China',
            language: body.language || 'Indonesia',
            cast: JSON.stringify([]),
        }).returning({ id: dramas.id, title: dramas.title });

        return c.json({ id: created.id, title: created.title, already_exists: false }, 201);
    } catch (error) {
        console.error('Admin create drama error:', error);
        return c.json({ error: 'Failed to create drama' }, 500);
    }
});

// ==================== UPSERT EPISODE (scraper use) ====================
adminRoute.post('/dramas/:dramaId/episodes', async (c) => {
    try {
        const { dramaId } = c.req.param();
        const body = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const epNo = body.episodeNumber;
        if (!epNo) return c.json({ error: 'episodeNumber is required' }, 400);
        if (!body.videoUrl) return c.json({ error: 'videoUrl is required' }, 400);

        const drama = await db.select({ id: dramas.id }).from(dramas).where(eq(dramas.id, dramaId)).limit(1).then((r: any[]) => r[0]);
        if (!drama) return c.json({ error: 'Drama not found' }, 404);

        const existing = await db.select({ id: episodes.id })
            .from(episodes)
            .where(and(eq(episodes.dramaId, dramaId), eq(episodes.episodeNumber, epNo)))
            .limit(1).then((r: any[]) => r[0]);

        if (existing) {
            await db.update(episodes).set({
                videoUrl: body.videoUrl,
                ...(body.videoUrl540p ? { videoUrl540p: body.videoUrl540p } : {}),
                ...(body.isActive !== undefined ? { isActive: body.isActive } : {}),
                ...(body.coinPrice !== undefined ? { coinPrice: body.coinPrice } : {}),
                updatedAt: new Date(),
            }).where(eq(episodes.id, existing.id));
            return c.json({ id: existing.id, updated: true });
        }

        const [created] = await db.insert(episodes).values({
            dramaId,
            episodeNumber: epNo,
            title: body.title || `Episode ${epNo}`,
            videoUrl: body.videoUrl,
            videoUrl540p: body.videoUrl540p || null,
            duration: 0,
            isVip: body.isVip || false,
            coinPrice: body.coinPrice || 0,
            views: 0,
            isActive: body.isActive !== undefined ? body.isActive : false,
        }).returning({ id: episodes.id });

        return c.json({ id: created.id, updated: false }, 201);
    } catch (error) {
        console.error('Admin upsert episode error:', error);
        return c.json({ error: 'Failed to upsert episode' }, 500);
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
        if (body.cover !== undefined) updateData.cover = body.cover;
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
        const results: Record<string, boolean> = {};

        // Add video_url_540p column if not exists
        try {
            await db.execute(sql`ALTER TABLE episodes ADD COLUMN IF NOT EXISTS video_url_540p text`);
            results.episodes_540p = true;
        } catch (e: any) {
            results.episodes_540p = false;
        }

        // Add last_seen column if not exists (for online tracking)
        try {
            await db.execute(sql`ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW()`);
            results.users_last_seen = true;
        } catch (e: any) {
            results.users_last_seen = false;
        }

        // Backfill last_seen from updated_at for existing rows
        try {
            await db.execute(sql`UPDATE users SET last_seen = updated_at WHERE last_seen IS NULL`);
            results.backfill_last_seen = true;
        } catch (e: any) {
            results.backfill_last_seen = false;
        }

        // Verify columns exist
        const check = await db.execute(sql`
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'last_seen'
        `);
        const lastSeenExists = (check as any).rows && (check as any).rows.length > 0;

        return c.json({
            ok: lastSeenExists,
            results,
            message: lastSeenExists
                ? 'Migration complete: last_seen column exists, online tracking active (5 min threshold)'
                : 'Migration may have failed - check DB manually',
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


