import { Hono } from 'hono';
import { eq, and, desc, like, or, sql, asc } from 'drizzle-orm';
import { getDb, parseJsonArray, toJsonArray } from '../db';
import { dramas, episodes, seasons } from '../db/schema';
import type { Env } from '../middleware/auth';

const dramasRoute = new Hono<Env>();

// Helper to enrich drama with parsed arrays
function enrichDrama(d: typeof dramas.$inferSelect) {
    return {
        ...d,
        genres: parseJsonArray(d.genres),
        tagList: parseJsonArray(d.tagList),
        cast: parseJsonArray(d.cast),
    };
}

// POST /api/dramas - Create/register a drama (scraper)
dramasRoute.post('/', async (c) => {
    try {
        const body = await c.req.json();
        const { title, description, cover, genres, status, country, language } = body;
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        if (!title) return c.json({ error: 'Title is required' }, 400);

        if (description && description.length < 10) {
            return c.json({ error: 'Description too short (min 10 chars)' }, 400);
        }

        // Check cover URL (skip for R2 URLs - we control those uploads)
        if (cover && !cover.includes('.r2.dev') && !cover.includes('.r2.cloudflarestorage.com')) {
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
                    status: status || existing.status,
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
            status: status || 'ongoing',
            country: country || 'China',
            language: language || 'Indonesia',
            isActive: true,
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
            .orderBy(desc(dramas.createdAt))
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
        const total = totalResult[0]?.count || 0;

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
                    .where(and(eq(episodes.dramaId, drama.id), eq(episodes.isActive, true)))
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

        // Get all active dramas with their first episode (Drizzle ORM - PostgreSQL compatible)
        const allDramas = await db.select().from(dramas)
            .where(eq(dramas.isActive, true))
            .orderBy(desc(dramas.views))
            .limit(500); // cap at 500 for feed pool

        // Fetch first episode for each drama (batch)
        const results = await Promise.all(
            allDramas.map(async (drama) => {
                const firstEp = await db.select().from(episodes)
                    .where(and(
                        eq(episodes.dramaId, drama.id),
                        eq(episodes.isActive, true),
                    ))
                    .orderBy(asc(episodes.episodeNumber))
                    .limit(1)
                    .then((r: any[]) => r[0]);

                if (!firstEp?.videoUrl) return null;
                return {
                    ...enrichDrama(drama),
                    episodes: [{
                        id: firstEp.id,
                        videoUrl: firstEp.videoUrl,
                        episodeNumber: firstEp.episodeNumber,
                        title: firstEp.title,
                        duration: firstEp.duration,
                    }],
                };
            })
        );

        const available = results.filter(Boolean) as NonNullable<typeof results[0]>[];


        // Seeded shuffle
        const seedNum = parseInt(seed) || Date.now();
        const shuffled = [...available];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(((seedNum * (i + 1) * 9301 + 49297) % 233280) / 233280 * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }

        // Paginate
        const start = (page - 1) * limit;
        const pageItems = shuffled.slice(start, start + limit);
        const hasMore = start + limit < shuffled.length;

        return c.json({
            dramas: pageItems,
            page,
            hasMore,
            total: shuffled.length,
        });
    } catch (error) {
        console.error('Get feed error:', error);
        return c.json({ error: 'Failed to get feed' }, 500);
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

        return c.json(result.map(enrichDrama));
    } catch (error) {
        console.error('Get new dramas error:', error);
        return c.json({ error: 'Failed to get new dramas' }, 500);
    }
});

// GET /api/dramas/banners
dramasRoute.get('/banners', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const result = await db.select().from(dramas)
            .where(and(eq(dramas.isActive, true), eq(dramas.isFeatured, true)))
            .orderBy(desc(dramas.updatedAt))
            .limit(10);

        return c.json(result.map(enrichDrama));
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
                like(dramas.title, searchTerm),
                like(dramas.description, searchTerm),
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
            total: totalResult[0]?.count || 0,
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

        // Get episodes
        const eps = await db.select().from(episodes)
            .where(and(eq(episodes.dramaId, id), eq(episodes.isActive, true)))
            .orderBy(asc(episodes.episodeNumber));

        return c.json({
            ...enrichDrama(drama),
            episodes: eps,
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
            .where(and(eq(episodes.dramaId, dramaId), eq(episodes.isActive, true)))
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
                .where(and(eq(episodes.dramaId, dramaId), eq(episodes.isActive, true)))
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
                        eq(episodes.isActive, true),
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
dramasRoute.delete('/:id', async (c) => {
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
dramasRoute.patch('/:id', async (c) => {
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
        if (typeof body.isActive === 'boolean') updates.isActive = body.isActive;
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

        return c.json(enrichDrama(updated));
    } catch (error) {
        console.error('Patch drama error:', error);
        return c.json({ error: 'Failed to update drama' }, 500);
    }
});

// POST /api/dramas/bulk-complete - Mark all ongoing → completed
dramasRoute.post('/bulk-complete', async (c) => {
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
dramasRoute.post('/bulk-publish', async (c) => {
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
                .set({ isActive: true, updatedAt: new Date() })
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
