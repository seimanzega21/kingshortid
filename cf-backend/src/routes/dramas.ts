import { Hono } from 'hono';
import { eq, and, desc, like, ilike, or, sql, asc, gte, inArray } from 'drizzle-orm';
import { getDb, parseJsonArray, toJsonArray } from '../db';
import { dramas, episodes, seasons, subtitles, watchHistory } from '../db/schema';
import { sendBroadcastNotification } from '../services/fcm';
import { requireAdmin, getAuthUser } from '../middleware/auth';
import type { Env } from '../middleware/auth';

const dramasRoute = new Hono<Env>();

// Helper to enrich drama with parsed arrays
function enrichDrama(d: typeof dramas.$inferSelect) {
    let finalCover = d.cover;
    if (finalCover && finalCover.startsWith('/api/uploads')) {
        finalCover = `https://admin.shortlovers.id${finalCover}`;
    }

    return {
        ...d,
        cover: finalCover,
        genres: parseJsonArray(d.genres),
        tagList: parseJsonArray(d.tagList),
        cast: parseJsonArray(d.cast),
    };
}

// POST /api/dramas - Create/register a drama (scraper)
dramasRoute.post('/', requireAdmin, async (c) => {
    try {
        const body = await c.req.json();
        const { title, description, cover, genres, status, country, language } = body;
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        if (!title) return c.json({ error: 'Title is required' }, 400);

        if (description && description.length < 10) {
            return c.json({ error: 'Description too short (min 10 chars)' }, 400);
        }

        // Check cover URL (skip for R2/CDN URLs - we control those uploads)
        if (cover && !cover.includes('.r2.dev') && !cover.includes('.r2.cloudflarestorage.com') && !cover.includes('shortlovers.id') && !cover.includes('mydramawave.com')) {
            try {
                const resp = await fetch(cover, { method: 'HEAD', signal: AbortSignal.timeout(10000) });
                if (!resp.ok) return c.json({ error: 'Cover URL is not accessible' }, 400);
            } catch {
                return c.json({ error: 'Cover URL is not accessible' }, 400);
            }
        }

        const existing = await db.select().from(dramas).where(eq(dramas.title, title)).limit(1).then((r: any[]) => r[0]);

        if (existing) {
            const [updated] = await db.update(dramas)
                .set({
                    description: description || existing.description,
                    cover: cover || existing.cover,
                    genres: genres ? toJsonArray(genres) : existing.genres,
                    // Never let scraper overwrite admin-set status — admin controls publishing
                    country: country || existing.country,
                    language: language || existing.language,
                    updatedAt: new Date(),
                })
                .where(eq(dramas.id, existing.id))
                .returning();

            return c.json(enrichDrama(updated));
        }

        const [drama] = await db.insert(dramas).values({
            title,
            description: description || 'No description available',
            cover: cover || '',
            genres: toJsonArray(genres),
            // Always default to 'pending' — admin manually publishes via admin panel
            status: 'pending',
            country: country || 'China',
            language: language || 'Indonesia',
            isActive: false, // Never auto-activate from scraper
            views: 0,
            rating: 0,
            totalEpisodes: 0,
        }).returning();

        return c.json(enrichDrama(drama), 201);
    } catch (error) {
        console.error('Create drama error:', error);
        return c.json({ error: 'Failed to create drama' }, 500);
    }
});

// GET /api/dramas - List with pagination
dramasRoute.get('/', async (c) => {
    try {
        const page = parseInt(c.req.query('page') || '1');
        const limit = parseInt(c.req.query('limit') || '20');
        const genre = c.req.query('genre');
        const status = c.req.query('status');
        const includeInactive = c.req.query('includeInactive') === 'true';
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const whereClause = includeInactive ? undefined : eq(dramas.isActive, true);

        let query = db.select().from(dramas)
            .orderBy(desc(dramas.updatedAt))
            .limit(limit)
            .offset((page - 1) * limit);

        if (whereClause) {
            query = query.where(whereClause) as typeof query;
        }

        const allDramas = await query;

        const countQuery = db.select({ count: sql<number>`count(*)` }).from(dramas);
        const totalResult = whereClause
            ? await countQuery.where(whereClause)
            : await countQuery;
        const total = Number(totalResult[0]?.count || 0);

        return c.json({
            dramas: allDramas.map(enrichDrama),
            total,
            page,
            limit,
        });
    } catch (error) {
        console.error('Get dramas error:', error);
        return c.json({ error: 'Failed to get dramas' }, 500);
    }
});

// GET /api/dramas/trending
dramasRoute.get('/trending', async (c) => {
    try {
        const limit = parseInt(c.req.query('limit') || '10');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const result = await db.select().from(dramas)
            .where(eq(dramas.isActive, true))
            .orderBy(desc(dramas.views), desc(dramas.rating))
            .limit(limit);

        // Include first episode's videoUrl for each drama
        const enriched = await Promise.all(
            result.map(async (drama) => {
                const firstEp = await db.select()
                    .from(episodes)
                    .where(and(eq(episodes.dramaId, drama.id), sql`${episodes.videoUrl} IS NOT NULL`))
                    .orderBy(asc(episodes.episodeNumber))
                    .limit(1).then((r: any[]) => r[0]);


                return {
                    ...enrichDrama(drama),
                    episodes: firstEp ? [firstEp] : [],
                };
            })
        );

        return c.json(enriched);
    } catch (error) {
        console.error('Get trending error:', error);
        return c.json({ error: 'Failed to get trending dramas' }, 500);
    }
});

// GET /api/dramas/feed - Shuffled paginated feed (trending + new + random mix)
dramasRoute.get('/feed', async (c) => {
    try {
        const page = parseInt(c.req.query('page') || '1');
        const limit = parseInt(c.req.query('limit') || '15');
        const seed = c.req.query('seed') || '0';
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        // Optional User Personalization - Get user from JWT
        const user = await getAuthUser(c);
        const userId = user?.id;

        // 1. Fetch recent views map (popularity over last 7 days)
        const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
        const recentViews = await db.select({
            dramaId: watchHistory.dramaId,
            count: sql<number>`count(${watchHistory.id})`
        })
        .from(watchHistory)
        .where(gte(watchHistory.watchedAt, sevenDaysAgo))
        .groupBy(watchHistory.dramaId);

        const recentViewsMap = new Map<string, number>();
        recentViews.forEach(rv => recentViewsMap.set(rv.dramaId, Number(rv.count) || 0));

        // 2. Fetch watch history of the user to apply penalty (de-prioritization)
        const userHistory: any[] = userId 
            ? await db.select().from(watchHistory).where(eq(watchHistory.userId, userId))
            : [];
        const watchedDramaIds = new Set<string>(userHistory.map(h => h.dramaId));

        // 3. Get all active dramas (up to 500 for the feed pool)
        const allDramas = await db.select().from(dramas)
            .where(eq(dramas.isActive, true))
            .limit(500);

        // 4. Fetch first episode for each drama in a single optimized query
        const firstEpisodes = await db.execute(sql`
            SELECT DISTINCT ON (drama_id) id, drama_id, video_url, episode_number, title, duration
            FROM episodes
            WHERE video_url IS NOT NULL
            ORDER BY drama_id, episode_number ASC
        `);

        const firstEpMap = new Map<string, any>();
        for (const ep of firstEpisodes as any[]) {
            const dramaId = ep.drama_id || ep.dramaId;
            if (dramaId) {
                firstEpMap.set(dramaId, {
                    id: ep.id,
                    videoUrl: ep.video_url || ep.videoUrl,
                    episodeNumber: ep.episode_number || ep.episodeNumber,
                    title: ep.title,
                    duration: ep.duration,
                });
            }
        }

        const results = allDramas.map((drama) => {
            const firstEp = firstEpMap.get(drama.id);
            if (!firstEp) return null;
            return {
                ...enrichDrama(drama),
                episodes: [firstEp],
            };
        });

        const available = results.filter(Boolean) as NonNullable<typeof results[0]>[];

        // 5. Calculate Score for each drama
        const now = Date.now();
        const seedNum = parseInt(seed) || Math.floor(now / (24 * 60 * 60 * 1000));
        
        // Seeded random generator
        const getSeededRandom = (s: number) => {
            return () => {
                const x = Math.sin(s++) * 10000;
                return x - Math.floor(x);
            };
        };
        const random = getSeededRandom(seedNum);

        const dramasWithScores = available.map(item => {
            // A. Recency Score (R) - max 100
            const ageInDays = Math.max(0, (now - new Date(item.createdAt).getTime()) / (1000 * 60 * 60 * 24));
            const recencyScore = Math.max(0, 100 - ageInDays);

            // B. Recent Popularity Score (P) - max 100
            const rvCount = recentViewsMap.get(item.id) || 0;
            const popularityScore = Math.min(100, rvCount * 10); // 10 unique users in 7d = 100 points

            // C. Quality Score (Q) - max 100
            const ratingVal = Number(item.rating) || 4.5;
            const qualityScore = Math.min(100, ratingVal * 20);

            // D. Combined base score (Quality 40%, Popularity 30%, Recency 30%)
            const baseScore = (qualityScore * 0.4) + (popularityScore * 0.3) + (recencyScore * 0.3);

            // E. Apply watch history penalty (started: -200, completed: -1000)
            let penalty = 0;
            if (watchedDramaIds.has(item.id)) {
                const hRecord = userHistory.find(h => h.dramaId === item.id);
                const watchedEpisode = hRecord?.episodeNumber || 1;
                const totalEpisodes = item.totalEpisodes || 1;

                if (watchedEpisode >= totalEpisodes) {
                    penalty = 1000; // Tamat
                } else {
                    penalty = 200; // Sedang ditonton
                }
            }

            // F. Daily Seeded Random offset (-30 to +30)
            const randomOffset = (random() * 60 - 30);

            const finalScore = baseScore - penalty + randomOffset;

            return {
                item,
                finalScore,
            };
        });

        // 6. Sort by final score
        const sortedFeed = dramasWithScores
            .sort((a, b) => b.finalScore - a.finalScore)
            .map(x => x.item);

        // 7. Paginate
        const start = (page - 1) * limit;
        const pageItems = sortedFeed.slice(start, start + limit);
        const hasMore = start + limit < sortedFeed.length;

        return c.json({
            dramas: pageItems,
            page,
            hasMore,
            total: sortedFeed.length,
        });
    } catch (error: any) {
        console.error('Get feed error:', error);
        return c.json({ error: 'Failed to get feed', msg: error.message, stack: error.stack }, 500);
    }
});

// GET /api/dramas/new
dramasRoute.get('/new', async (c) => {
    try {
        const limit = parseInt(c.req.query('limit') || '10');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const result = await db.select().from(dramas)
            .where(eq(dramas.isActive, true))
            .orderBy(desc(dramas.createdAt))
            .limit(limit);

        // Include firstVideoUrl for each drama
        const enriched = await Promise.all(
            result.map(async (drama) => {
                const firstEp = await db.select({ videoUrl: episodes.videoUrl })
                    .from(episodes)
                    .where(and(eq(episodes.dramaId, drama.id), sql`${episodes.videoUrl} IS NOT NULL`))
                    .orderBy(asc(episodes.episodeNumber))
                    .limit(1).then((r: any[]) => r[0]);
                return {
                    ...enrichDrama(drama),
                    firstVideoUrl: firstEp?.videoUrl || null,
                };
            })
        );

        return c.json(enriched);
    } catch (error) {
        console.error('Get new dramas error:', error);
        return c.json({ error: 'Failed to get new dramas' }, 500);
    }
});

// GET /api/dramas/banners
dramasRoute.get('/banners', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        // Fetch settings
        const settingsRows = await db.execute(sql`SELECT key, value FROM app_settings WHERE key IN ('bannerMode', 'bannerRotationDays')`);
        let bannerMode = 'auto';
        let rotationDays = 2;
        for (const row of settingsRows as any[]) {
            if (row.key === 'bannerMode') bannerMode = row.value;
            if (row.key === 'bannerRotationDays') rotationDays = parseInt(row.value) || 2;
        }

        // 1. Fetch admin's manual picks
        const featured = await db.select().from(dramas)
            .where(and(eq(dramas.isActive, true), eq(dramas.isFeatured, true)))
            .orderBy(desc(dramas.updatedAt))
            .limit(10);

        let finalBanners = [...featured];

        // 2. If 'auto' mode and less than 10, fill the rest automatically
        if (bannerMode === 'auto' && finalBanners.length < 10) {
            const limitNeeded = 10 - finalBanners.length;
            
            // Pool of active non-featured dramas, trending first
            const pool = await db.select().from(dramas)
                .where(and(eq(dramas.isActive, true), eq(dramas.isFeatured, false)))
                .orderBy(desc(dramas.views), desc(dramas.createdAt))
                .limit(40); // larger pool to shuffle

            // Seeded shuffle that changes every N days
            const seedNum = Math.floor(Date.now() / (Math.max(1, rotationDays) * 24 * 60 * 60 * 1000));
            const shuffled = [...pool];
            for (let i = shuffled.length - 1; i > 0; i--) {
                const j = Math.floor(((seedNum * (i + 1) * 9301 + 49297) % 233280) / 233280 * (i + 1));
                [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
            }

            finalBanners = [...finalBanners, ...shuffled.slice(0, limitNeeded)];
        }

        return c.json(finalBanners.map(enrichDrama));
    } catch (error) {
        console.error('Get banners error:', error);
        return c.json({ error: 'Failed to get banners' }, 500);
    }
});

// GET /api/dramas/search
dramasRoute.get('/search', async (c) => {
    try {
        const query = c.req.query('q') || '';
        const page = parseInt(c.req.query('page') || '1');
        const limit = parseInt(c.req.query('limit') || '20');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        if (!query) return c.json({ dramas: [], total: 0, page });

        const searchTerm = `%${query}%`;
        const whereClause = and(
            eq(dramas.isActive, true),
            or(
                ilike(dramas.title, searchTerm),
                ilike(dramas.description, searchTerm),
            ),
        );

        const [results, totalResult] = await Promise.all([
            db.select().from(dramas)
                .where(whereClause!)
                .orderBy(desc(dramas.views))
                .limit(limit)
                .offset((page - 1) * limit),
            db.select({ count: sql<number>`count(*)` }).from(dramas)
                .where(whereClause!),
        ]);

        return c.json({
            dramas: results.map(enrichDrama),
            total: Number(totalResult[0]?.count || 0),
            page,
        });
    } catch (error) {
        console.error('Search error:', error);
        return c.json({ error: 'Search failed' }, 500);
    }
});

// GET /api/dramas/:id
dramasRoute.get('/:id', async (c) => {
    try {
        const id = c.req.param('id');
        const includeInactive = c.req.query('includeInactive') === 'true';
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const whereClause = includeInactive
            ? eq(dramas.id, id)
            : and(eq(dramas.id, id), eq(dramas.isActive, true));

        const drama = await db.select().from(dramas)
            .where(whereClause)
            .limit(1).then((r: any[]) => r[0]);

        if (!drama) return c.json({ error: 'Drama not found' }, 404);

        // Get episodes - return all that have videoUrl ready
        // Drama.isActive controls visibility, episodes are ready when videoUrl exists
        const eps = await db.select().from(episodes)
            .where(and(
                eq(episodes.dramaId, id),
                sql`${episodes.videoUrl} IS NOT NULL`
            ))
            .orderBy(asc(episodes.episodeNumber));

        // Attach subtitles to all episodes in a single query
        const episodeIds = eps.map(e => e.id);
        let allSubtitles: any[] = [];
        if (episodeIds.length > 0) {
            allSubtitles = await db.select()
                .from(subtitles)
                .where(inArray(subtitles.episodeId, episodeIds));
        }

        const epsWithSubs = eps.map(ep => ({
            ...ep,
            subtitles: allSubtitles.filter(s => s.episodeId === ep.id)
        }));

        return c.json({
            ...enrichDrama(drama),
            episodes: epsWithSubs,
        });
    } catch (error) {
        console.error('Get drama error:', error);
        return c.json({ error: 'Failed to get drama' }, 500);
    }
});

// GET /api/dramas/:id/episodes
dramasRoute.get('/:id/episodes', async (c) => {
    try {
        const dramaId = c.req.param('id');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const eps = await db.select().from(episodes)
            .where(and(
                eq(episodes.dramaId, dramaId),
                sql`${episodes.videoUrl} IS NOT NULL`
            ))
            .orderBy(asc(episodes.episodeNumber));

        return c.json(eps);
    } catch (error) {
        console.error('Get episodes error:', error);
        return c.json({ error: 'Failed to get episodes' }, 500);
    }
});

// GET /api/dramas/:id/episodes/:episodeNumber
dramasRoute.get('/:id/episodes/:episodeNumber', async (c) => {
    try {
        const dramaId = c.req.param('id');
        const episodeNum = parseInt(c.req.param('episodeNumber'));
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const episode = await db.select().from(episodes)
            .where(and(
                eq(episodes.dramaId, dramaId),
                eq(episodes.episodeNumber, episodeNum),
            ))
            .limit(1).then((r: any[]) => r[0]);

        if (!episode) return c.json({ error: 'Episode not found' }, 404);

        return c.json(episode);
    } catch (error) {
        console.error('Get episode error:', error);
        return c.json({ error: 'Failed to get episode' }, 500);
    }
});

// POST /api/dramas/:id/view — increment views counter (fire-and-forget, no auth)
dramasRoute.post('/:id/view', async (c) => {
    try {
        const id = c.req.param('id');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        await db.update(dramas)
            .set({ views: sql`${dramas.views} + 1` })
            .where(eq(dramas.id, id));
        return c.json({ ok: true });
    } catch {
        return c.json({ ok: false }, 500);
    }
});

// GET /api/dramas/:id/seasons
dramasRoute.get('/:id/seasons', async (c) => {
    try {
        const dramaId = c.req.param('id');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const seasonList = await db.select().from(seasons)
            .where(eq(seasons.dramaId, dramaId))
            .orderBy(asc(seasons.seasonNumber));

        if (seasonList.length === 0) {
            // No seasons, return all episodes as single season
            const eps = await db.select().from(episodes)
                .where(and(eq(episodes.dramaId, dramaId), sql`${episodes.videoUrl} IS NOT NULL`))
                .orderBy(asc(episodes.episodeNumber));

            return c.json([{
                id: 'default',
                seasonNumber: 1,
                title: 'Season 1',
                episodes: eps,
            }]);
        }

        // Get episodes for each season
        const seasonsWithEpisodes = await Promise.all(
            seasonList.map(async (season) => {
                const eps = await db.select().from(episodes)
                    .where(and(
                        eq(episodes.dramaId, dramaId),
                        eq(episodes.seasonId, season.id),
                        sql`${episodes.videoUrl} IS NOT NULL`,
                    ))
                    .orderBy(asc(episodes.episodeNumber));
                return { ...season, episodes: eps };
            })
        );

        return c.json(seasonsWithEpisodes);
    } catch (error) {
        console.error('Get seasons error:', error);
        return c.json({ error: 'Failed to get seasons' }, 500);
    }
});

// DELETE /api/dramas/:id - Delete a drama and its episodes
dramasRoute.delete('/:id', requireAdmin, async (c) => {
    try {
        const id = c.req.param('id');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const drama = await db.select().from(dramas).where(eq(dramas.id, id)).limit(1).then((r: any[]) => r[0]);
        if (!drama) return c.json({ error: 'Drama not found' }, 404);

        // Delete all episodes first
        await db.delete(episodes).where(eq(episodes.dramaId, id));
        // Delete the drama
        await db.delete(dramas).where(eq(dramas.id, id));

        return c.json({ message: `Deleted drama '${drama.title}' and its episodes` });
    } catch (error) {
        console.error('Delete drama error:', error);
        return c.json({ error: 'Failed to delete drama' }, 500);
    }
});

// PATCH /api/dramas/:id - Update drama fields by ID
dramasRoute.patch('/:id', requireAdmin, async (c) => {
    try {
        const id = c.req.param('id');
        const body = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const existing = await db.select().from(dramas).where(eq(dramas.id, id)).limit(1).then((r: any[]) => r[0]);
        if (!existing) return c.json({ error: 'Drama not found' }, 404);

        const updates: Record<string, unknown> = { updatedAt: new Date() };
        if (body.cover) updates.cover = body.cover;
        if (body.title) updates.title = body.title;
        if (body.description) updates.description = body.description;
        if (body.status) updates.status = body.status;
        if (typeof body.views === 'number') updates.views = body.views;
        if (typeof body.likes === 'number') updates.likes = body.likes;
        if (typeof body.isActive === 'boolean') {
            updates.isActive = body.isActive;
            // Set createdAt to now when publishing for the first time, to bump to top of "Baru Rilis"
            if (existing.isActive === false && body.isActive === true) {
                updates.createdAt = new Date();
            }
        }
        if (typeof body.isFeatured === 'boolean') updates.isFeatured = body.isFeatured;
        if (typeof body.isVip === 'boolean') updates.isVip = body.isVip;
        if (body.genres) updates.genres = toJsonArray(body.genres);
        if (body.tagList) updates.tagList = toJsonArray(body.tagList);
        if (body.cast) updates.cast = toJsonArray(body.cast);
        if (body.director !== undefined) updates.director = body.director;
        if (body.country) updates.country = body.country;
        if (body.language) updates.language = body.language;
        if (body.banner !== undefined) updates.banner = body.banner;
        if (typeof body.rating === 'number') updates.rating = body.rating;
        if (typeof body.totalEpisodes === 'number') updates.totalEpisodes = body.totalEpisodes;

        const [updated] = await db.update(dramas)
            .set(updates)
            .where(eq(dramas.id, id))
            .returning();

        // ─── TRIGGER: New Release Broadcast Notification ───
        // UPDATE (April 2026): Dinonaktifkan sementara atas permintaan user
        // agar tidak terjadi spam notifikasi saat banyak drama diaktifkan sekaligus.
        // Notifikasi rilis baru sekarang dikirim secara manual via Kotak Pesan / Notifikasi Admin.
        /*
        if (existing.isActive === false && body.isActive === true) {
            // Kickoff in background
            void sendBroadcastNotification(
                c.env.SUPABASE_URL,
                c.env.SUPABASE_DB_PASSWORD,
                '🔥 Drama Baru Telah Rilis!',
                `${updated.title} kini sudah tayang. Tonton episode pertamanya sekarang!`,
                { dramaId: updated.id },
                updated.cover,
                'DRAMA_ACTION' // Pass custom action category (Putar button)
            );
        }
        */

        return c.json(enrichDrama(updated));
    } catch (error) {
        console.error('Patch drama error:', error);
        return c.json({ error: 'Failed to update drama' }, 500);
    }
});

// POST /api/dramas/bulk-complete - Mark all ongoing → completed
dramasRoute.post('/bulk-complete', requireAdmin, async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const ongoing = await db.select({ id: dramas.id }).from(dramas)
            .where(eq(dramas.status, 'ongoing'));

        let count = 0;
        for (const d of ongoing) {
            await db.update(dramas)
                .set({ status: 'completed', updatedAt: new Date() })
                .where(eq(dramas.id, d.id));
            count++;
        }

        return c.json({ message: `${count} dramas marked as completed`, count });
    } catch (error) {
        console.error('Bulk complete error:', error);
        return c.json({ error: 'Failed to complete dramas' }, 500);
    }
});

// POST /api/dramas/bulk-publish - Activate all ready dramas
dramasRoute.post('/bulk-publish', requireAdmin, async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const inactive = await db.select().from(dramas)
            .where(eq(dramas.isActive, false));

        const ready: string[] = [];
        const notReady: Array<{ title: string; issues: string[] }> = [];

        for (const d of inactive) {
            const issues: string[] = [];
            if (!d.cover || d.cover.length < 5) issues.push('NO_COVER');
            if (!d.description || d.description.length < 10 || d.description === d.title) issues.push('BAD_DESC');
            if (d.totalEpisodes === 0) issues.push('NO_EPISODES');

            if (issues.length === 0) {
                ready.push(d.id);
            } else {
                notReady.push({ title: d.title, issues });
            }
        }

        for (const id of ready) {
            await db.update(dramas)
                .set({ isActive: true, updatedAt: new Date(), createdAt: new Date() })
                .where(eq(dramas.id, id));
        }

        return c.json({
            message: `${ready.length} dramas published, ${notReady.length} still have issues`,
            published: ready.length,
            remaining: notReady.length,
            notReady,
        });
    } catch (error) {
        console.error('Bulk publish error:', error);
        return c.json({ error: 'Failed to publish dramas' }, 500);
    }
});

export default dramasRoute;
