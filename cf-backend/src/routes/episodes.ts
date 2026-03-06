import { Hono } from 'hono';
import { eq, and, sql, asc, desc } from 'drizzle-orm';
import { getDb } from '../db';
import { episodes, dramas, subtitles } from '../db/schema';
import type { Env } from '../middleware/auth';

const episodesRoute = new Hono<Env>();

// POST /api/episodes - Register episode (scraper)
episodesRoute.post('/', async (c) => {
    try {
        const { dramaId, episodeNumber, title, videoUrl, duration } = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        if (!dramaId || !episodeNumber || !videoUrl) {
            return c.json({ error: 'dramaId, episodeNumber, and videoUrl are required' }, 400);
        }

        // Validate video URL (skip for R2 URLs - we control those uploads)
        if (!videoUrl.includes('.r2.dev') && !videoUrl.includes('.r2.cloudflarestorage.com')) {
            try {
                const videoCheck = await fetch(videoUrl, { method: 'HEAD', signal: AbortSignal.timeout(10000) });
                if (!videoCheck.ok) {
                    return c.json({ error: `Video URL returned ${videoCheck.status}` }, 400);
                }
            } catch {
                return c.json({ error: 'Video URL is not accessible' }, 400);
            }
        }

        // Check if episode exists
        const existing = await db.select().from(episodes)
            .where(and(
                eq(episodes.dramaId, dramaId),
                eq(episodes.episodeNumber, parseInt(episodeNumber)),
            ))
            .limit(1).then((r: any[]) => r[0]);

        let episode;
        if (existing) {
            [episode] = await db.update(episodes)
                .set({
                    videoUrl,
                    title: title || existing.title,
                    duration: duration ? parseInt(duration) : existing.duration,
                    updatedAt: new Date(),
                })
                .where(eq(episodes.id, existing.id))
                .returning();
        } else {
            [episode] = await db.insert(episodes).values({
                dramaId,
                episodeNumber: parseInt(episodeNumber),
                title: title || `Episode ${episodeNumber}`,
                videoUrl,
                duration: duration ? parseInt(duration) : 0,
                isActive: true,
                isVip: false,
                coinPrice: 0,
                views: 0,
            }).returning();
        }

        // Update totalEpisodes count
        const countResult = await db.select({ count: sql<number>`count(*)` }).from(episodes)
            .where(eq(episodes.dramaId, dramaId));

        await db.update(dramas)
            .set({ totalEpisodes: countResult[0]?.count || 0, updatedAt: new Date() })
            .where(eq(dramas.id, dramaId));

        return c.json(episode, 201);
    } catch (error) {
        console.error('Create episode error:', error);
        return c.json({ error: 'Failed to create episode' }, 500);
    }
});

// GET /api/episodes/:id/stream
episodesRoute.get('/:id/stream', async (c) => {
    try {
        const id = c.req.param('id');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const episode = await db.select().from(episodes).where(eq(episodes.id, id)).limit(1).then((r: any[]) => r[0]);
        if (!episode) return c.json({ error: 'Episode not found' }, 404);

        // VIP check
        if (episode.isVip) {
            const authHeader = c.req.header('Authorization');
            if (!authHeader) {
                return c.json({
                    error: 'VIP content requires authentication',
                    isVip: true,
                    coinPrice: episode.coinPrice,
                }, 401);
            }
        }

        // Increment views
        await db.update(episodes)
            .set({ views: sql`${episodes.views} + 1` })
            .where(eq(episodes.id, id));

        // Get drama title
        const drama = await db.select({ title: dramas.title }).from(dramas)
            .where(eq(dramas.id, episode.dramaId)).limit(1).then((r: any[]) => r[0]);

        const expiresAt = new Date(Date.now() + 4 * 60 * 60 * 1000);

        return c.json({
            url: episode.videoUrl,
            expiresAt: expiresAt.toISOString(),
            duration: episode.duration,
            title: episode.title,
            episodeNumber: episode.episodeNumber,
            dramaTitle: drama?.title || '',
        });
    } catch (error) {
        console.error('Get stream error:', error);
        return c.json({ error: 'Failed to get stream URL' }, 500);
    }
});

// GET /api/episodes/:id/subtitles
episodesRoute.get('/:id/subtitles', async (c) => {
    try {
        const id = c.req.param('id');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const subs = await db.select().from(subtitles)
            .where(eq(subtitles.episodeId, id))
            .orderBy(desc(subtitles.isDefault), asc(subtitles.language));

        return c.json({ subtitles: subs });
    } catch (error) {
        console.error('Get subtitles error:', error);
        return c.json({ error: 'Failed to get subtitles' }, 500);
    }
});

// POST /api/episodes/:id/subtitles - Register subtitle (scraper)
episodesRoute.post('/:id/subtitles', async (c) => {
    try {
        const id = c.req.param('id');
        const { language, label, url, isDefault } = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        if (!language || !url) {
            return c.json({ error: 'language and url are required' }, 400);
        }

        const episode = await db.select().from(episodes).where(eq(episodes.id, id)).limit(1).then((r: any[]) => r[0]);
        if (!episode) return c.json({ error: 'Episode not found' }, 404);

        // Upsert: check if subtitle for this episode+language exists
        const existing = await db.select().from(subtitles)
            .where(and(eq(subtitles.episodeId, id), eq(subtitles.language, language)))
            .limit(1).then((r: any[]) => r[0]);

        let subtitle;
        if (existing) {
            [subtitle] = await db.update(subtitles)
                .set({ url, label: label || existing.label })
                .where(eq(subtitles.id, existing.id))
                .returning();
        } else {
            [subtitle] = await db.insert(subtitles).values({
                episodeId: id,
                language,
                label: label || language,
                url,
                isDefault: isDefault || false,
            }).returning();
        }

        return c.json(subtitle, 201);
    } catch (error) {
        console.error('Create subtitle error:', error);
        return c.json({ error: 'Failed to create subtitle' }, 500);
    }
});

// PATCH /api/episodes/:id - Update episode fields
episodesRoute.patch('/:id', async (c) => {
    try {
        const id = c.req.param('id');
        const body = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const existing = await db.select().from(episodes).where(eq(episodes.id, id)).limit(1).then((r: any[]) => r[0]);
        if (!existing) return c.json({ error: 'Episode not found' }, 404);

        const updates: Record<string, unknown> = { updatedAt: new Date() };
        if (body.episodeNumber !== undefined) updates.episodeNumber = parseInt(body.episodeNumber);
        if (body.videoUrl) updates.videoUrl = body.videoUrl;
        if (body.duration !== undefined) updates.duration = parseInt(body.duration);
        if (body.title) updates.title = body.title;

        const [updated] = await db.update(episodes)
            .set(updates)
            .where(eq(episodes.id, id))
            .returning();

        return c.json(updated);
    } catch (error) {
        console.error('Patch episode error:', error);
        return c.json({ error: 'Failed to update episode' }, 500);
    }
});

// DELETE /api/episodes/:id - Delete episode and update drama count
episodesRoute.delete('/:id', async (c) => {
    try {
        const id = c.req.param('id');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const episode = await db.select().from(episodes).where(eq(episodes.id, id)).limit(1).then((r: any[]) => r[0]);
        if (!episode) return c.json({ error: 'Episode not found' }, 404);

        // Delete the episode
        await db.delete(episodes).where(eq(episodes.id, id));

        // Update totalEpisodes count
        const countResult = await db.select({ count: sql<number>`count(*)` }).from(episodes)
            .where(eq(episodes.dramaId, episode.dramaId));
        await db.update(dramas)
            .set({ totalEpisodes: countResult[0]?.count || 0, updatedAt: new Date() })
            .where(eq(dramas.id, episode.dramaId));

        return c.json({ success: true, message: 'Episode deleted' });
    } catch (error) {
        console.error('Delete episode error:', error);
        return c.json({ error: 'Failed to delete episode' }, 500);
    }
});
// POST /api/episodes/shift - Shift episode numbers for a drama
// Body: { dramaId, startFrom: number, shiftBy: number }
// Shifts all episodes with episodeNumber >= startFrom by shiftBy
episodesRoute.post('/shift', async (c) => {
    try {
        const { dramaId, startFrom, shiftBy } = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        if (!dramaId || startFrom === undefined || !shiftBy) {
            return c.json({ error: 'dramaId, startFrom, and shiftBy are required' }, 400);
        }

        // Get all episodes that need shifting, ordered descending to avoid conflicts
        const toShift = await db.select().from(episodes)
            .where(and(
                eq(episodes.dramaId, dramaId),
                sql`${episodes.episodeNumber} >= ${startFrom}`,
            ))
            .orderBy(desc(episodes.episodeNumber));

        let shifted = 0;
        for (const ep of toShift) {
            await db.update(episodes)
                .set({
                    episodeNumber: ep.episodeNumber + parseInt(shiftBy),
                    updatedAt: new Date(),
                })
                .where(eq(episodes.id, ep.id));
            shifted++;
        }

        // Update totalEpisodes count
        const countResult = await db.select({ count: sql<number>`count(*)` }).from(episodes)
            .where(eq(episodes.dramaId, dramaId));
        await db.update(dramas)
            .set({ totalEpisodes: countResult[0]?.count || 0, updatedAt: new Date() })
            .where(eq(dramas.id, dramaId));

        return c.json({ shifted, message: `Shifted ${shifted} episodes by ${shiftBy}` });
    } catch (error) {
        console.error('Shift episodes error:', error);
        return c.json({ error: 'Failed to shift episodes' }, 500);
    }
});

export default episodesRoute;
