import sys

new_endpoints = '''
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
            isActive: true,
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
            isVip: false,
            coinPrice: 0,
            views: 0,
            isActive: true,
        }).returning({ id: episodes.id });

        return c.json({ id: created.id, updated: false }, 201);
    } catch (error) {
        console.error('Admin upsert episode error:', error);
        return c.json({ error: 'Failed to upsert episode' }, 500);
    }
});

'''

path = 'd:\\kingshortid\\cf-backend\\src\\routes\\admin.ts'
content = open(path, encoding='utf-8').read()

# Insert before UPDATE DRAMA section
target = '// ==================== UPDATE DRAMA ===================='
if target not in content:
    print("ERROR: target not found!")
    sys.exit(1)

new_content = content.replace(target, new_endpoints + target, 1)
open(path, 'w', encoding='utf-8').write(new_content)
print("SUCCESS: endpoints added")
